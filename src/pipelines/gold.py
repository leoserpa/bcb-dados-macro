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
    macro_path = gold_root / "macro_indicators.parquet"
    ptax_daily_path = gold_root / "ptax_daily.parquet"
    temporary_macro = gold_root / "macro_indicators.tmp.parquet"
    temporary_ptax = gold_root / "ptax_daily.tmp.parquet"

    for stale_path in (temporary_database, temporary_macro, temporary_ptax):
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
                PARTITION BY fonte, indicador_id, periodo_referencia, metrica
            )
            """
        )

        _copy_table_to_parquet(connection, "macro_indicators", temporary_macro)
        _copy_table_to_parquet(connection, "ptax_daily", temporary_ptax)
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    temporary_macro.replace(macro_path)
    temporary_ptax.replace(ptax_daily_path)
    temporary_database.replace(database_path)


def _copy_table_to_parquet(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    target: Path,
) -> None:
    escaped_target = str(target).replace("'", "''")
    connection.execute(
        f"COPY {table_name} TO '{escaped_target}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
