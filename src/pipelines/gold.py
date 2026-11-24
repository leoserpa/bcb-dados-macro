"""Build business-ready DuckDB and Parquet assets from the Silver layer."""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl


def build_gold(
    *,
    sgs_path: Path,
    focus_path: Path,
    ptax_path: Path,
    gold_root: Path,
) -> None:
    """Atomically rebuild the analytical serving layer."""
    gold_root.mkdir(parents=True, exist_ok=True)
    database_path = gold_root / "bcb_macro.duckdb"
    temporary_database = gold_root / "bcb_macro.tmp.duckdb"
    temporary_database_wal = gold_root / "bcb_macro.tmp.duckdb.wal"
    macro_path = gold_root / "macro_indicators.parquet"
    ptax_daily_path = gold_root / "ptax_daily.parquet"
    temporary_macro = gold_root / "macro_indicators.tmp.parquet"
    temporary_ptax = gold_root / "ptax_daily.tmp.parquet"
    temp_paths = (
        temporary_database,
        temporary_database_wal,
        temporary_macro,
        temporary_ptax,
    )

    for stale_path in temp_paths:
        stale_path.unlink(missing_ok=True)

    connection = duckdb.connect(str(temporary_database))
    try:
        connection.register("_sgs", pl.read_parquet(sgs_path))
        connection.register("_focus", pl.read_parquet(focus_path))
        connection.register("_ptax", pl.read_parquet(ptax_path))

        connection.execute("CREATE TABLE sgs_series AS SELECT * FROM _sgs")
        connection.execute("CREATE TABLE focus_expectations AS SELECT * FROM _focus")
        connection.execute("CREATE TABLE ptax_quotes AS SELECT * FROM _ptax")

        connection.execute(
            """
            CREATE TABLE macro_indicators AS
            SELECT
                'SGS' AS fonte,
                CAST(codigo_serie AS VARCHAR) AS indicador_id,
                nome_serie AS indicador,
                data AS data_observacao,
                strftime(data, '%Y-%m-%d') AS periodo_referencia,
                'observado' AS metrica,
                valor,
                frequencia AS detalhe,
                ingested_at
            FROM sgs_series
            UNION ALL
            SELECT
                'FOCUS' AS fonte,
                indicador AS indicador_id,
                indicador,
                data AS data_observacao,
                data_referencia AS periodo_referencia,
                'mediana_expectativa' AS metrica,
                mediana AS valor,
                concat_ws(
                    ' | ',
                    indicador_detalhe,
                    concat('base=', CAST(coalesce(base_calculo, -1) AS VARCHAR))
                ) AS detalhe,
                ingested_at
            FROM focus_expectations
            """
        )
        connection.execute(
            """
            CREATE TABLE ptax_daily AS
            SELECT
                data_referencia,
                moeda,
                cotacao_compra,
                cotacao_venda,
                paridade_compra,
                paridade_venda,
                tipo_boletim,
                data_hora_cotacao,
                ingested_at
            FROM ptax_quotes
            QUALIFY row_number() OVER (
                PARTITION BY data_referencia, moeda
                ORDER BY
                    CASE WHEN tipo_boletim = 'Fechamento' THEN 0 ELSE 1 END,
                    data_hora_cotacao DESC
            ) = 1
            """
        )
        connection.execute(
            """
            CREATE VIEW vw_macro_latest AS
            SELECT *
            FROM macro_indicators
            QUALIFY data_observacao = max(data_observacao) OVER (
                PARTITION BY
                    fonte,
                    indicador_id,
                    CASE WHEN fonte = 'SGS' THEN '' ELSE periodo_referencia END,
                    metrica,
                    detalhe
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE ptax_risk_metrics AS
            WITH returns AS (
                SELECT
                    data_referencia,
                    moeda,
                    cotacao_compra,
                    cotacao_venda,
                    cotacao_venda - cotacao_compra AS spread,
                    LN(
                        cotacao_venda / NULLIF(
                            LAG(cotacao_venda) OVER (PARTITION BY moeda ORDER BY data_referencia),
                            0
                        )
                    ) AS log_return
                FROM ptax_daily
            )
            SELECT
                data_referencia,
                moeda,
                cotacao_compra,
                cotacao_venda,
                spread,
                (EXP(log_return) - 1) * 100 AS retorno_diario_pct,
                AVG(cotacao_venda) OVER (
                    PARTITION BY moeda
                    ORDER BY data_referencia
                    ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
                ) AS media_movel_21d,
                AVG(cotacao_venda) OVER (
                    PARTITION BY moeda
                    ORDER BY data_referencia
                    ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
                ) AS media_movel_252d,
                STDDEV_SAMP(log_return) OVER (
                    PARTITION BY moeda
                    ORDER BY data_referencia
                    ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
                ) * SQRT(252) * 100 AS vol_anualizada_21d,
                (
                    cotacao_venda - AVG(cotacao_venda) OVER (
                        PARTITION BY moeda
                        ORDER BY data_referencia
                        ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
                    )
                ) / NULLIF(
                    STDDEV_SAMP(cotacao_venda) OVER (
                        PARTITION BY moeda
                        ORDER BY data_referencia
                        ROWS BETWEEN 251 PRECEDING AND CURRENT ROW
                    ),
                    0
                ) AS zscore_252d
            FROM returns
            """
        )
        connection.execute(
            """
            CREATE VIEW vw_focus_repricing AS
            WITH base0 AS (
                SELECT
                    indicador,
                    data_referencia,
                    data,
                    mediana,
                    media,
                    desvio_padrao,
                    numero_respondentes,
                    LAG(mediana, 21) OVER (
                        PARTITION BY indicador, data_referencia
                        ORDER BY data
                    ) AS mediana_30d_atras
                FROM focus_expectations
                WHERE base_calculo = 0 AND indicador_detalhe = ''
            ),
            latest_b0 AS (
                SELECT * FROM base0
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY indicador, data_referencia
                    ORDER BY data DESC
                ) = 1
            ),
            latest_b1 AS (
                SELECT
                    indicador,
                    data_referencia,
                    data AS data_b1,
                    mediana AS mediana_b1,
                    desvio_padrao AS desvio_b1
                FROM focus_expectations
                WHERE base_calculo = 1 AND indicador_detalhe = ''
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY indicador, data_referencia
                    ORDER BY data DESC
                ) = 1
            )
            SELECT
                b0.indicador,
                b0.data_referencia,
                b0.data AS data_base0,
                b0.mediana AS mediana_base0,
                b1.mediana_b1 AS mediana_base1,
                b1.mediana_b1 - b0.mediana AS repricing_b1_vs_b0,
                b0.mediana - b0.mediana_30d_atras AS drift_30d,
                b0.desvio_padrao,
                b0.numero_respondentes
            FROM latest_b0 b0
            LEFT JOIN latest_b1 b1
                ON b0.indicador = b1.indicador
               AND b0.data_referencia = b1.data_referencia
            """
        )
        connection.execute(
            """
            CREATE VIEW vw_macro_regime AS
            WITH selic_meta AS (
                SELECT data, valor AS selic_meta
                FROM sgs_series
                WHERE codigo_serie = 432
            ),
            ipca_cur AS (
                SELECT
                    data,
                    mediana AS ipca_focus_ano,
                    row_number() OVER (PARTITION BY data ORDER BY data_referencia) AS rn
                FROM focus_expectations
                WHERE indicador = 'IPCA'
                  AND base_calculo = 0
                  AND indicador_detalhe = ''
                  AND TRY_CAST(data_referencia AS INTEGER) = YEAR(data)
            ),
            ipca_day AS (
                SELECT data, ipca_focus_ano FROM ipca_cur WHERE rn = 1
            )
            SELECT
                s.data,
                s.selic_meta,
                i.ipca_focus_ano,
                ((1 + s.selic_meta / 100.0) / (1 + i.ipca_focus_ano / 100.0) - 1) * 100.0
                    AS juro_real_ex_ante,
                CASE
                    WHEN ((1 + s.selic_meta / 100.0) / (1 + i.ipca_focus_ano / 100.0) - 1) * 100.0
                         >= 6.0 THEN 'Restritivo'
                    WHEN ((1 + s.selic_meta / 100.0) / (1 + i.ipca_focus_ano / 100.0) - 1) * 100.0
                         >= 3.5 THEN 'Neutro'
                    ELSE 'Expansionista'
                END AS regime_monetario
            FROM selic_meta s
            INNER JOIN ipca_day i ON s.data = i.data
            """
        )

        _copy_table_to_parquet(connection, "macro_indicators", temporary_macro)
        _copy_table_to_parquet(connection, "ptax_daily", temporary_ptax)
        connection.execute("CHECKPOINT")
    except Exception:
        connection.close()
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)
        raise
    connection.close()

    try:
        temporary_database.replace(database_path)
        temporary_macro.replace(macro_path)
        temporary_ptax.replace(ptax_daily_path)
    except Exception:
        for temp_path in temp_paths:
            temp_path.unlink(missing_ok=True)
        raise
    finally:
        temporary_database_wal.unlink(missing_ok=True)


def _copy_table_to_parquet(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    target: Path,
) -> None:
    escaped_target = str(target).replace("'", "''")
    connection.execute(
        f"COPY {table_name} TO '{escaped_target}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
