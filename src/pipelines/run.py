"""End-to-end orchestration for the BCB Medallion pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import requests

from src.extractors.olinda import OlindaExtractor
from src.extractors.sgs import SGS_SERIES, ExtractionError, SGSExtractor
from src.pipelines.gold import build_gold
from src.transformers.medallion import (
    FOCUS_SCHEMA,
    PTAX_SCHEMA,
    SGS_SCHEMA,
    transform_focus,
    transform_ptax,
    transform_sgs,
    upsert_parquet,
)
from src.utils.http_client import create_http_session
from src.utils.logging_config import configure_logging
from src.utils.storage import write_bronze_json

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INITIAL_DATE = date(2010, 1, 1)


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Runtime options for incremental ingestion."""

    data_root: Path
    start_date: date | None
    end_date: date
    lookback_days: int = 7
    currency: str = "USD"


def run_pipeline(config: PipelineConfig) -> dict[str, int | bool | str | list[str]]:
    """Execute extraction, Silver upserts and conditional Gold rebuild."""
    if config.lookback_days < 0:
        raise ValueError("lookback_days deve ser maior ou igual a zero")

    bronze_root = config.data_root / "bronze"
    silver_root = config.data_root / "silver"
    gold_root = config.data_root / "gold"
    sgs_path = silver_root / "sgs" / "sgs.parquet"
    focus_path = silver_root / "focus" / "focus.parquet"
    ptax_path = silver_root / "ptax" / "ptax.parquet"

    initial_date = date.fromisoformat(
        os.getenv("BCB_INITIAL_DATE", DEFAULT_INITIAL_DATE.isoformat())
    )
    ingestion_date = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    ingested_at = datetime.now(UTC)

    session = create_http_session()
    sgs_extractor = SGSExtractor(session)
    olinda_extractor = OlindaExtractor(session)
    failed_sources: list[str] = []
    try:
        sgs_frames: list[pl.DataFrame] = []
        for code, definition in SGS_SERIES.items():
            series_start = config.start_date or _incremental_start(
                sgs_path,
                date_column="data",
                initial_date=initial_date,
                lookback_days=config.lookback_days,
                filter_expression=pl.col("codigo_serie") == code,
            )
            _validate_interval(series_start, config.end_date)
            LOGGER.info("Extraindo SGS %s de %s a %s", code, series_start, config.end_date)
            try:
                raw_sgs = sgs_extractor.fetch_series(code, series_start, config.end_date)
            except (requests.RequestException, ExtractionError) as error:
                failed_sources.append(f"sgs:{code}")
                LOGGER.warning(
                    "SGS %s indisponível; preservando dados anteriores: %s",
                    code,
                    error,
                )
                continue
            write_bronze_json(
                bronze_root,
                source="sgs",
                ingestion_date=ingestion_date,
                file_name=f"series_{code}.json",
                records=raw_sgs,
                request_metadata={
                    "codigo_serie": code,
                    "data_inicial": series_start.isoformat(),
                    "data_final": config.end_date.isoformat(),
                },
            )
            sgs_frames.append(
                transform_sgs(
                    raw_sgs,
                    code=code,
                    name=definition.name,
                    frequency=definition.frequency,
                    ingested_at=ingested_at,
                )
            )

        incoming_sgs = (
            pl.concat(sgs_frames, how="vertical_relaxed")
            if sgs_frames
            else pl.DataFrame(schema=SGS_SCHEMA)
        )
        final_sgs, sgs_changed = upsert_parquet(
            incoming_sgs,
            sgs_path,
            primary_key=["data", "codigo_serie"],
            sort_by=["codigo_serie", "data"],
            retain_rows=pl.col("codigo_serie").is_in(list(SGS_SERIES)),
        )

        focus_start = config.start_date or _incremental_start(
            focus_path,
            date_column="data",
            initial_date=initial_date,
            lookback_days=config.lookback_days,
        )
        _validate_interval(focus_start, config.end_date)
        LOGGER.info("Extraindo Focus de %s a %s", focus_start, config.end_date)
        try:
            raw_focus = olinda_extractor.fetch_focus(focus_start, config.end_date)
            write_bronze_json(
                bronze_root,
                source="focus",
                ingestion_date=ingestion_date,
                file_name="expectativas_anuais.json",
                records=raw_focus,
                request_metadata={
                    "data_inicial": focus_start.isoformat(),
                    "data_final": config.end_date.isoformat(),
                },
            )
            incoming_focus = transform_focus(raw_focus, ingested_at=ingested_at)
        except (requests.RequestException, ExtractionError) as error:
            failed_sources.append("focus")
            LOGGER.warning("Focus indisponível; preservando dados anteriores: %s", error)
            incoming_focus = pl.DataFrame(schema=FOCUS_SCHEMA)
        final_focus, focus_changed = upsert_parquet(
            incoming_focus,
            focus_path,
            primary_key=[
                "data",
                "indicador",
                "data_referencia",
                "indicador_detalhe",
                "base_calculo",
            ],
            sort_by=["indicador", "data_referencia", "data"],
        )

        ptax_start = config.start_date or _incremental_start(
            ptax_path,
            date_column="data_referencia",
            initial_date=initial_date,
            lookback_days=config.lookback_days,
        )
        _validate_interval(ptax_start, config.end_date)
        LOGGER.info("Extraindo PTAX %s de %s a %s", config.currency, ptax_start, config.end_date)
        try:
            raw_ptax = olinda_extractor.fetch_ptax(ptax_start, config.end_date, config.currency)
            write_bronze_json(
                bronze_root,
                source="ptax",
                ingestion_date=ingestion_date,
                file_name=f"cotacoes_{config.currency.lower()}.json",
                records=raw_ptax,
                request_metadata={
                    "moeda": config.currency.upper(),
                    "data_inicial": ptax_start.isoformat(),
                    "data_final": config.end_date.isoformat(),
                },
            )
            incoming_ptax = transform_ptax(
                raw_ptax,
                currency=config.currency,
                ingested_at=ingested_at,
            )
        except (requests.RequestException, ExtractionError) as error:
            failed_sources.append("ptax")
            LOGGER.warning("PTAX indisponível; preservando dados anteriores: %s", error)
            incoming_ptax = pl.DataFrame(schema=PTAX_SCHEMA)
        final_ptax, ptax_changed = upsert_parquet(
            incoming_ptax,
            ptax_path,
            primary_key=["data_hora_cotacao", "moeda", "tipo_boletim"],
            sort_by=["moeda", "data_hora_cotacao", "tipo_boletim"],
        )
    finally:
        session.close()

    gold_missing = not (gold_root / "bcb_macro.duckdb").exists()
    silver_changed = sgs_changed or focus_changed or ptax_changed
    if silver_changed or gold_missing:
        LOGGER.info("Reconstruindo camada Gold")
        build_gold(
            sgs_path=sgs_path,
            focus_path=focus_path,
            ptax_path=ptax_path,
            gold_root=gold_root,
        )
    else:
        LOGGER.info("Sem alterações na Silver; camada Gold preservada")

    return {
        "end_date": config.end_date.isoformat(),
        "sgs_rows": final_sgs.height,
        "focus_rows": final_focus.height,
        "ptax_rows": final_ptax.height,
        "silver_changed": silver_changed,
        "gold_rebuilt": silver_changed or gold_missing,
        "failed_sources": failed_sources,
    }


def _incremental_start(
    path: Path,
    *,
    date_column: str,
    initial_date: date,
    lookback_days: int,
    filter_expression: pl.Expr | None = None,
) -> date:
    if not path.exists():
        return initial_date

    columns = [date_column, "codigo_serie"] if filter_expression is not None else [date_column]
    frame = pl.read_parquet(path, columns=columns)
    if filter_expression is not None:
        frame = frame.filter(filter_expression)
    if frame.is_empty():
        return initial_date

    latest_date = frame.get_column(date_column).max()
    if latest_date is None:
        return initial_date
    return max(initial_date, latest_date - timedelta(days=lookback_days))


def _validate_interval(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        start = start_date.isoformat()
        end = end_date.isoformat()
        raise ValueError(f"Intervalo inválido: início {start} após fim {end}")


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("use o formato YYYY-MM-DD") from error


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface."""
    parser = argparse.ArgumentParser(description="Pipeline Medallion de dados do BCB")
    parser.add_argument("--start-date", type=_parse_date, help="Data inicial YYYY-MM-DD")
    parser.add_argument(
        "--end-date",
        type=_parse_date,
        default=datetime.now(ZoneInfo("America/Sao_Paulo")).date(),
        help="Data final YYYY-MM-DD",
    )
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--data-root", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--log-dir", type=Path, default=PROJECT_ROOT / "logs")
    return parser


def main() -> None:
    """CLI entrypoint."""
    arguments = build_parser().parse_args()
    configure_logging(arguments.log_dir)
    summary = run_pipeline(
        PipelineConfig(
            data_root=arguments.data_root,
            start_date=arguments.start_date,
            end_date=arguments.end_date,
            lookback_days=arguments.lookback_days,
            currency=arguments.currency,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    failed_sources = summary["failed_sources"]
    if failed_sources:
        LOGGER.error("Pipeline parcial; fontes com falha: %s", ", ".join(failed_sources))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
