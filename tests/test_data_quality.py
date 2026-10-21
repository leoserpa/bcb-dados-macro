from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import pytest

from src.pipelines.quality import validate_database


@pytest.fixture
def valid_database(tmp_path: Path) -> Path:
    database = tmp_path / "quality.duckdb"
    connection = duckdb.connect(str(database))
    try:
        connection.execute(
            """
            CREATE TABLE sgs_series (
                data DATE,
                codigo_serie BIGINT,
                nome_serie VARCHAR,
                frequencia VARCHAR,
                valor DOUBLE,
                ingested_at TIMESTAMPTZ
            );
            INSERT INTO sgs_series
            SELECT DATE '2026-10-20', code, 'Série', 'diaria', 1.0, now()
            FROM unnest([11, 432, 13762, 13967, 13970, 13982, 20631, 21082, 24364]) AS t(code);

            CREATE TABLE focus_expectations (
                indicador VARCHAR,
                indicador_detalhe VARCHAR,
                data DATE,
                data_referencia VARCHAR,
                media DOUBLE,
                mediana DOUBLE,
                desvio_padrao DOUBLE,
                minimo DOUBLE,
                maximo DOUBLE,
                numero_respondentes BIGINT,
                base_calculo BIGINT,
                ingested_at TIMESTAMPTZ
            );
            INSERT INTO focus_expectations
            SELECT indicador, '', DATE '2026-10-20', '2026', 10.0, 10.0,
                   0.1, 9.0, 11.0, 100, 0, now()
            FROM unnest(['IPCA', 'Selic', 'Câmbio', 'PIB Total']) AS t(indicador);

            CREATE TABLE ptax_quotes (
                moeda VARCHAR,
                data_hora_cotacao TIMESTAMP,
                data_referencia DATE,
                cotacao_compra DOUBLE,
                cotacao_venda DOUBLE,
                paridade_compra DOUBLE,
                paridade_venda DOUBLE,
                tipo_boletim VARCHAR,
                ingested_at TIMESTAMPTZ
            );
            INSERT INTO ptax_quotes VALUES (
                'USD', TIMESTAMP '2026-10-20 13:00:00', DATE '2026-10-20',
                5.0, 5.1, 1.0, 1.0, 'Fechamento', now()
            );

            CREATE TABLE macro_indicators AS
            SELECT codigo_serie::VARCHAR AS indicador_id FROM sgs_series
            UNION ALL
            SELECT indicador AS indicador_id FROM focus_expectations;
            CREATE TABLE ptax_daily AS SELECT * FROM ptax_quotes;
            CREATE VIEW vw_macro_latest AS SELECT * FROM macro_indicators;
            """
        )
    finally:
        connection.close()
    return database


def _check(report, name: str):
    return next(check for check in report.checks if check.name == name)


def test_valid_database_passes_all_quality_checks(valid_database: Path) -> None:
    report = validate_database(
        valid_database,
        as_of_date=date(2026, 10, 21),
        max_staleness_days=3,
    )

    assert report.passed
    assert all(check.passed for check in report.checks)


def test_missing_database_fails_quality_gate(tmp_path: Path) -> None:
    report = validate_database(tmp_path / "missing.duckdb")

    assert not report.passed
    assert _check(report, "database_exists").actual is False


def test_duplicate_primary_key_is_detected(valid_database: Path) -> None:
    connection = duckdb.connect(str(valid_database))
    try:
        connection.execute("INSERT INTO sgs_series SELECT * FROM sgs_series LIMIT 1")
    finally:
        connection.close()

    report = validate_database(valid_database, as_of_date=date(2026, 10, 21))

    assert not report.passed
    assert _check(report, "sgs_primary_key_unique").actual == 1


def test_unexpected_focus_indicator_is_detected(valid_database: Path) -> None:
    connection = duckdb.connect(str(valid_database))
    try:
        connection.execute(
            """
            UPDATE focus_expectations
            SET indicador = 'IGP-M'
            WHERE indicador = 'IPCA'
            """
        )
    finally:
        connection.close()

    report = validate_database(valid_database, as_of_date=date(2026, 10, 21))

    assert not report.passed
    assert not _check(report, "focus_expected_indicators").passed


def test_stale_data_is_detected(valid_database: Path) -> None:
    report = validate_database(
        valid_database,
        as_of_date=date(2026, 11, 1),
        max_staleness_days=3,
    )

    assert not report.passed
    assert _check(report, "sgs_freshness").actual == 12
    assert _check(report, "focus_freshness").actual == 12
    assert _check(report, "ptax_freshness").actual == 12


def test_negative_staleness_limit_is_rejected(valid_database: Path) -> None:
    with pytest.raises(ValueError, match="maior ou igual a zero"):
        validate_database(valid_database, max_staleness_days=-1)


def test_missing_required_column_is_reported(valid_database: Path) -> None:
    connection = duckdb.connect(str(valid_database))
    try:
        connection.execute("ALTER TABLE sgs_series DROP COLUMN valor")
    finally:
        connection.close()

    report = validate_database(valid_database, as_of_date=date(2026, 10, 21))

    assert not report.passed
    assert _check(report, "sgs_series_required_columns").actual == ["valor"]


def test_missing_latest_date_fails_freshness_without_crashing(valid_database: Path) -> None:
    connection = duckdb.connect(str(valid_database))
    try:
        connection.execute("UPDATE sgs_series SET data = NULL")
    finally:
        connection.close()

    report = validate_database(
        valid_database,
        as_of_date=date(2026, 10, 21),
        max_staleness_days=3,
    )

    assert not report.passed
    assert _check(report, "sgs_freshness").actual is None
