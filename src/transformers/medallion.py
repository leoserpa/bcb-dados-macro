"""Bronze-to-Silver transformations and idempotent Parquet upserts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl

from src.models.schemas import FocusRecord, PTAXRecord, SGSRecord

SGS_SCHEMA: dict[str, pl.DataType] = {
    "data": pl.Date,
    "codigo_serie": pl.Int64,
    "nome_serie": pl.String,
    "frequencia": pl.String,
    "valor": pl.Float64,
    "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
}

FOCUS_SCHEMA: dict[str, pl.DataType] = {
    "indicador": pl.String,
    "indicador_detalhe": pl.String,
    "data": pl.Date,
    "data_referencia": pl.String,
    "media": pl.Float64,
    "mediana": pl.Float64,
    "desvio_padrao": pl.Float64,
    "minimo": pl.Float64,
    "maximo": pl.Float64,
    "numero_respondentes": pl.Int64,
    "base_calculo": pl.Int64,
    "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
}

PTAX_SCHEMA: dict[str, pl.DataType] = {
    "moeda": pl.String,
    "data_hora_cotacao": pl.Datetime(time_unit="us"),
    "data_referencia": pl.Date,
    "cotacao_compra": pl.Float64,
    "cotacao_venda": pl.Float64,
    "paridade_compra": pl.Float64,
    "paridade_venda": pl.Float64,
    "tipo_boletim": pl.String,
    "ingested_at": pl.Datetime(time_unit="us", time_zone="UTC"),
}


def transform_sgs(
    raw_records: list[dict[str, Any]],
    *,
    code: int,
    name: str,
    frequency: str,
    ingested_at: datetime,
) -> pl.DataFrame:
    """Validate, normalize and type SGS observations."""
    records = [
        SGSRecord.model_validate(
            {
                **raw_record,
                "codigo_serie": code,
                "nome_serie": name,
                "frequencia": frequency,
                "ingested_at": ingested_at,
            }
        ).model_dump()
        for raw_record in raw_records
    ]
    return _frame_from_records(records, SGS_SCHEMA)


def transform_focus(
    raw_records: list[dict[str, Any]],
    *,
    ingested_at: datetime,
) -> pl.DataFrame:
    """Validate, normalize and type annual Focus expectations."""
    records = [
        FocusRecord.model_validate({**raw_record, "ingested_at": ingested_at}).model_dump()
        for raw_record in raw_records
    ]
    return _frame_from_records(records, FOCUS_SCHEMA).with_columns(
        pl.col("indicador_detalhe").fill_null(""),
        pl.col("base_calculo").fill_null(-1),
    )


def transform_ptax(
    raw_records: list[dict[str, Any]],
    *,
    currency: str,
    ingested_at: datetime,
) -> pl.DataFrame:
    """Validate, normalize and type PTAX bulletins."""
    records = [
        PTAXRecord.model_validate(
            {**raw_record, "moeda": currency.upper(), "ingested_at": ingested_at}
        ).model_dump()
        for raw_record in raw_records
    ]
    return _frame_from_records(records, PTAX_SCHEMA)


def upsert_parquet(
    incoming: pl.DataFrame,
    target: Path,
    *,
    primary_key: list[str],
    sort_by: list[str],
    retain_rows: pl.Expr | None = None,
) -> tuple[pl.DataFrame, bool]:
    """Upsert by primary key while avoiding rewrites for identical business data."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = pl.read_parquet(target)
        if incoming.is_empty():
            return existing, False
        combined = pl.concat([existing, incoming], how="diagonal_relaxed")
    else:
        existing = None
        combined = incoming

    if retain_rows is not None:
        combined = combined.filter(retain_rows)

    content_columns = [column for column in combined.columns if column != "ingested_at"]
    final = (
        combined.sort("ingested_at")
        .unique(subset=content_columns, keep="first", maintain_order=True)
        .sort("ingested_at")
        .unique(subset=primary_key, keep="last", maintain_order=True)
        .sort(sort_by)
    )

    changed = existing is None or not existing.sort(sort_by).equals(final)
    if changed:
        temporary = target.with_suffix(".tmp.parquet")
        final.write_parquet(temporary, compression="zstd", statistics=True)
        temporary.replace(target)
    return final, changed


def _frame_from_records(
    records: list[dict[str, Any]],
    schema: dict[str, pl.DataType],
) -> pl.DataFrame:
    if not records:
        return pl.DataFrame(schema=schema)
    return pl.from_dicts(records, schema=schema, strict=False)
