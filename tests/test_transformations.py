from __future__ import annotations

from datetime import UTC, datetime

import polars as pl

from src.transformers.medallion import (
    transform_focus,
    transform_ptax,
    transform_sgs,
    upsert_parquet,
)


def test_transform_sgs_enforces_date_and_float_types() -> None:
    frame = transform_sgs(
        [{"data": "20/10/2026", "valor": "1.234,56"}],
        code=11,
        name="Taxa Selic diária",
        frequency="diaria",
        ingested_at=datetime(2026, 10, 20, tzinfo=UTC),
    )

    assert frame.row(0, named=True)["data"].isoformat() == "2026-10-20"
    assert frame.row(0, named=True)["valor"] == 1234.56


def test_transform_focus_keeps_null_statistics() -> None:
    frame = transform_focus(
        [
            {
                "Indicador": "IPCA",
                "IndicadorDetalhe": None,
                "Data": "2026-10-20",
                "DataReferencia": "2027",
                "Media": None,
                "Mediana": "4,25",
                "numeroRespondentes": 100,
                "baseCalculo": 0,
            }
        ],
        ingested_at=datetime(2026, 10, 20, tzinfo=UTC),
    )

    record = frame.row(0, named=True)
    assert record["media"] is None
    assert record["mediana"] == 4.25
    assert record["data"].isoformat() == "2026-10-20"


def test_transform_ptax_derives_reference_date() -> None:
    frame = transform_ptax(
        [
            {
                "cotacaoCompra": 5.3,
                "cotacaoVenda": 5.31,
                "dataHoraCotacao": "2026-10-20T13:10:00",
                "tipoBoletim": "Fechamento",
            }
        ],
        currency="usd",
        ingested_at=datetime(2026, 10, 20, tzinfo=UTC),
    )

    record = frame.row(0, named=True)
    assert record["moeda"] == "USD"
    assert record["data_referencia"].isoformat() == "2026-10-20"


def test_upsert_is_idempotent_and_accepts_revisions(tmp_path) -> None:
    target = tmp_path / "sgs.parquet"
    original = transform_sgs(
        [{"data": "20/10/2026", "valor": "10.0"}],
        code=11,
        name="Taxa Selic diária",
        frequency="diaria",
        ingested_at=datetime(2026, 10, 20, 12, tzinfo=UTC),
    )
    _, first_changed = upsert_parquet(
        original,
        target,
        primary_key=["data", "codigo_serie"],
        sort_by=["codigo_serie", "data"],
    )

    identical = transform_sgs(
        [{"data": "20/10/2026", "valor": "10.0"}],
        code=11,
        name="Taxa Selic diária",
        frequency="diaria",
        ingested_at=datetime(2026, 10, 20, 13, tzinfo=UTC),
    )
    _, second_changed = upsert_parquet(
        identical,
        target,
        primary_key=["data", "codigo_serie"],
        sort_by=["codigo_serie", "data"],
    )

    revised = transform_sgs(
        [{"data": "20/10/2026", "valor": "10.1"}],
        code=11,
        name="Taxa Selic diária",
        frequency="diaria",
        ingested_at=datetime(2026, 10, 20, 14, tzinfo=UTC),
    )
    final, revision_changed = upsert_parquet(
        revised,
        target,
        primary_key=["data", "codigo_serie"],
        sort_by=["codigo_serie", "data"],
    )

    assert first_changed is True
    assert second_changed is False
    assert revision_changed is True
    assert final.height == 1
    assert final.get_column("valor").item() == 10.1


def test_upsert_can_remove_rows_from_deactivated_series(tmp_path) -> None:
    target = tmp_path / "sgs.parquet"
    existing = transform_sgs(
        [{"data": "01/01/2014", "valor": "10.0"}],
        code=2521,
        name="Série desativada",
        frequency="trimestral",
        ingested_at=datetime(2026, 10, 20, tzinfo=UTC),
    )
    upsert_parquet(
        existing,
        target,
        primary_key=["data", "codigo_serie"],
        sort_by=["codigo_serie", "data"],
    )
    replacement = transform_sgs(
        [{"data": "20/10/2026", "valor": "11.0"}],
        code=13967,
        name="Fluxo cambial comercial",
        frequency="diaria",
        ingested_at=datetime(2026, 10, 21, tzinfo=UTC),
    )

    final, changed = upsert_parquet(
        replacement,
        target,
        primary_key=["data", "codigo_serie"],
        sort_by=["codigo_serie", "data"],
        retain_rows=pl.col("codigo_serie") == 13967,
    )

    assert changed is True
    assert final.get_column("codigo_serie").to_list() == [13967]
