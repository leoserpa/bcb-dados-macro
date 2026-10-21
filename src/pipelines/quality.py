"""Data quality gates for the analytical DuckDB database."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "gold" / "bcb_macro.duckdb"
EXPECTED_TABLES = {
    "sgs_series",
    "focus_expectations",
    "ptax_quotes",
    "macro_indicators",
    "ptax_daily",
    "vw_macro_latest",
}
EXPECTED_SGS_SERIES = {11, 432, 13762, 13967, 13970, 13982, 20631, 21082, 24364}
EXPECTED_FOCUS_INDICATORS = {"IPCA", "Selic", "Câmbio", "PIB Total"}


@dataclass(frozen=True, slots=True)
class QualityCheck:
    """Result of one deterministic data quality assertion."""

    name: str
    passed: bool
    actual: Any
    expected: Any
    severity: str = "critical"


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Aggregated quality report returned by the validation command."""

    database: str
    checks: list[QualityCheck]

    @property
    def passed(self) -> bool:
        return all(check.passed or check.severity != "critical" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "database": self.database,
            "passed": self.passed,
            "checks": [asdict(check) for check in self.checks],
        }


def validate_database(
    database: Path,
    *,
    as_of_date: date | None = None,
    max_staleness_days: int | None = None,
) -> QualityReport:
    """Validate schema, completeness, uniqueness, validity and freshness."""
    checks: list[QualityCheck] = []
    if not database.exists():
        checks.append(QualityCheck("database_exists", False, False, True))
        return QualityReport(str(database), checks)
    if max_staleness_days is not None and max_staleness_days < 0:
        raise ValueError("max_staleness_days deve ser maior ou igual a zero")

    reference_date = as_of_date or date.today()
    connection = duckdb.connect(str(database), read_only=True)
    try:
        available_tables = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        }
        missing_tables = sorted(EXPECTED_TABLES - available_tables)
        checks.append(QualityCheck("required_tables", not missing_tables, missing_tables, []))
        if missing_tables:
            return QualityReport(str(database), checks)

        schema_valid = _add_table_checks(connection, checks)
        if not schema_valid:
            return QualityReport(str(database), checks)
        _add_domain_checks(connection, checks)
        _add_reconciliation_checks(connection, checks)
        _add_date_checks(connection, checks, reference_date, max_staleness_days)
    finally:
        connection.close()
    return QualityReport(str(database), checks)


def _add_table_checks(
    connection: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
) -> bool:
    required_columns = {
        "sgs_series": {"data", "codigo_serie", "valor", "ingested_at"},
        "focus_expectations": {
            "data",
            "indicador",
            "data_referencia",
            "mediana",
            "base_calculo",
            "ingested_at",
        },
        "ptax_quotes": {
            "data_hora_cotacao",
            "data_referencia",
            "moeda",
            "cotacao_compra",
            "cotacao_venda",
            "tipo_boletim",
            "ingested_at",
        },
    }
    schema_valid = True
    for table, expected_columns in required_columns.items():
        columns = {
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'main' AND table_name = ?",
                [table],
            ).fetchall()
        }
        missing_columns = sorted(expected_columns - columns)
        schema_valid = schema_valid and not missing_columns
        checks.append(
            QualityCheck(f"{table}_required_columns", not missing_columns, missing_columns, [])
        )

    for table in ("sgs_series", "focus_expectations", "ptax_quotes"):
        row_count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        checks.append(QualityCheck(f"{table}_not_empty", row_count > 0, row_count, "> 0"))

    if not schema_valid:
        return False

    null_queries = {
        "sgs_required_not_null": """
            SELECT COUNT(*) FROM sgs_series
            WHERE data IS NULL OR codigo_serie IS NULL OR valor IS NULL OR ingested_at IS NULL
        """,
        "focus_required_not_null": """
            SELECT COUNT(*) FROM focus_expectations
            WHERE data IS NULL OR indicador IS NULL OR data_referencia IS NULL
               OR mediana IS NULL OR ingested_at IS NULL
        """,
        "ptax_required_not_null": """
            SELECT COUNT(*) FROM ptax_quotes
            WHERE data_hora_cotacao IS NULL OR data_referencia IS NULL OR moeda IS NULL
               OR cotacao_compra IS NULL OR cotacao_venda IS NULL
               OR tipo_boletim IS NULL OR ingested_at IS NULL
        """,
    }
    for name, query in null_queries.items():
        count = connection.execute(query).fetchone()[0]
        checks.append(QualityCheck(name, count == 0, count, 0))

    duplicate_queries = {
        "sgs_primary_key_unique": """
            SELECT COUNT(*) - COUNT(DISTINCT (data, codigo_serie)) FROM sgs_series
        """,
        "focus_primary_key_unique": """
            SELECT COUNT(*) - COUNT(DISTINCT (
                data, indicador, data_referencia, indicador_detalhe, base_calculo
            )) FROM focus_expectations
        """,
        "ptax_primary_key_unique": """
            SELECT COUNT(*) - COUNT(DISTINCT (
                data_hora_cotacao, moeda, tipo_boletim
            )) FROM ptax_quotes
        """,
    }
    for name, query in duplicate_queries.items():
        count = connection.execute(query).fetchone()[0]
        checks.append(QualityCheck(name, count == 0, count, 0))
    return True


def _add_domain_checks(
    connection: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
) -> None:
    actual_series = {
        row[0]
        for row in connection.execute("SELECT DISTINCT codigo_serie FROM sgs_series").fetchall()
    }
    checks.append(
        QualityCheck(
            "sgs_expected_series",
            actual_series == EXPECTED_SGS_SERIES,
            sorted(actual_series),
            sorted(EXPECTED_SGS_SERIES),
        )
    )
    actual_indicators = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT indicador FROM focus_expectations"
        ).fetchall()
    }
    checks.append(
        QualityCheck(
            "focus_expected_indicators",
            actual_indicators == EXPECTED_FOCUS_INDICATORS,
            sorted(actual_indicators),
            sorted(EXPECTED_FOCUS_INDICATORS),
        )
    )

    finite_queries = {
        "sgs_values_finite": "SELECT COUNT(*) FROM sgs_series WHERE NOT isfinite(valor)",
        "focus_values_finite": """
            SELECT COUNT(*) FROM focus_expectations
            WHERE NOT isfinite(mediana) OR NOT isfinite(media)
        """,
        "ptax_values_finite": """
            SELECT COUNT(*) FROM ptax_quotes
            WHERE NOT isfinite(cotacao_compra) OR NOT isfinite(cotacao_venda)
        """,
    }
    for name, query in finite_queries.items():
        count = connection.execute(query).fetchone()[0]
        checks.append(QualityCheck(name, count == 0, count, 0))


def _add_reconciliation_checks(
    connection: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
) -> None:
    sgs_count, focus_count, macro_count = connection.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM sgs_series),
            (SELECT COUNT(*) FROM focus_expectations),
            (SELECT COUNT(*) FROM macro_indicators)
        """
    ).fetchone()
    checks.append(
        QualityCheck(
            "macro_row_count_reconciled",
            macro_count == sgs_count + focus_count,
            macro_count,
            sgs_count + focus_count,
        )
    )
    ptax_count, daily_count = connection.execute(
        "SELECT (SELECT COUNT(*) FROM ptax_quotes), (SELECT COUNT(*) FROM ptax_daily)"
    ).fetchone()
    checks.append(
        QualityCheck(
            "ptax_daily_row_count_valid",
            0 < daily_count <= ptax_count,
            daily_count,
            f"> 0 e <= {ptax_count}",
        )
    )


def _add_date_checks(
    connection: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
    reference_date: date,
    max_staleness_days: int | None,
) -> None:
    date_columns = {
        "sgs": ("sgs_series", "data"),
        "focus": ("focus_expectations", "data"),
        "ptax": ("ptax_quotes", "data_referencia"),
    }
    for source, (table, column) in date_columns.items():
        future_count = connection.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} > ?", [reference_date]
        ).fetchone()[0]
        checks.append(QualityCheck(f"{source}_no_future_dates", future_count == 0, future_count, 0))
        if max_staleness_days is not None:
            latest_date = connection.execute(f"SELECT MAX({column}) FROM {table}").fetchone()[0]
            if latest_date is None:
                checks.append(
                    QualityCheck(
                        f"{source}_freshness",
                        False,
                        None,
                        f"<= {max_staleness_days} dias",
                    )
                )
                continue
            age_days = (reference_date - latest_date).days
            checks.append(
                QualityCheck(
                    f"{source}_freshness",
                    age_days <= max_staleness_days,
                    age_days,
                    f"<= {max_staleness_days} dias",
                )
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Valida qualidade do DuckDB do BCB")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--as-of-date", type=date.fromisoformat)
    parser.add_argument("--max-staleness-days", type=int)
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    report = validate_database(
        arguments.database,
        as_of_date=arguments.as_of_date,
        max_staleness_days=arguments.max_staleness_days,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str))
    if not report.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
