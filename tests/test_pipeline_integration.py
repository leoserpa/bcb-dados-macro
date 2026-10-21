from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import duckdb
import polars as pl
import pytest
import requests

from src.extractors.sgs import SGS_SERIES
from src.pipelines.run import PipelineConfig, main, run_pipeline


class SessionStub:
    def close(self) -> None:
        pass


class SGSExtractorStub:
    def __init__(self, session: SessionStub) -> None:
        self.session = session

    def fetch_series(self, code: int, start_date: date, end_date: date) -> list[dict[str, str]]:
        return [{"data": end_date.strftime("%d/%m/%Y"), "valor": f"{code / 100:.2f}"}]


class OlindaExtractorStub:
    fail_focus = False

    def __init__(self, session: SessionStub) -> None:
        self.session = session

    def fetch_focus(self, start_date: date, end_date: date) -> list[dict[str, object]]:
        if self.fail_focus:
            raise requests.ConnectionError("Focus indisponível")
        return [
            {
                "Indicador": indicator,
                "IndicadorDetalhe": "",
                "Data": end_date.isoformat(),
                "DataReferencia": str(end_date.year),
                "Media": 10.0,
                "Mediana": 10.0,
                "DesvioPadrao": 0.1,
                "Minimo": 9.0,
                "Maximo": 11.0,
                "numeroRespondentes": 100,
                "baseCalculo": 0,
            }
            for indicator in ("IPCA", "Selic", "Câmbio", "PIB Total")
        ]

    def fetch_ptax(
        self,
        start_date: date,
        end_date: date,
        currency: str,
    ) -> list[dict[str, object]]:
        return [
            {
                "paridadeCompra": 1.0,
                "paridadeVenda": 1.0,
                "cotacaoCompra": 5.0,
                "cotacaoVenda": 5.1,
                "dataHoraCotacao": f"{end_date.isoformat()} 13:00:00.000",
                "tipoBoletim": "Fechamento",
            }
        ]


def _configure_stubs(monkeypatch) -> None:
    monkeypatch.setattr("src.pipelines.run.create_http_session", SessionStub)
    monkeypatch.setattr("src.pipelines.run.SGSExtractor", SGSExtractorStub)
    monkeypatch.setattr("src.pipelines.run.OlindaExtractor", OlindaExtractorStub)


def _config(data_root: Path) -> PipelineConfig:
    return PipelineConfig(
        data_root=data_root,
        start_date=date(2026, 10, 20),
        end_date=date(2026, 10, 20),
        lookback_days=7,
        currency="USD",
    )


def test_pipeline_builds_all_layers_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    _configure_stubs(monkeypatch)
    data_root = tmp_path / "data"

    first_run = run_pipeline(_config(data_root))
    second_run = run_pipeline(_config(data_root))

    assert first_run == {
        "end_date": "2026-10-20",
        "sgs_rows": len(SGS_SERIES),
        "focus_rows": 4,
        "ptax_rows": 1,
        "silver_changed": True,
        "gold_rebuilt": True,
        "failed_sources": [],
    }
    assert second_run["silver_changed"] is False
    assert second_run["gold_rebuilt"] is False

    sgs = pl.read_parquet(data_root / "silver" / "sgs" / "sgs.parquet")
    focus = pl.read_parquet(data_root / "silver" / "focus" / "focus.parquet")
    ptax = pl.read_parquet(data_root / "silver" / "ptax" / "ptax.parquet")
    assert sgs.height == len(SGS_SERIES)
    assert focus.height == 4
    assert ptax.height == 1

    database = data_root / "gold" / "bcb_macro.duckdb"
    connection = duckdb.connect(str(database), read_only=True)
    try:
        assert connection.execute("SELECT COUNT(*) FROM macro_indicators").fetchone()[0] == 13
        assert connection.execute("SELECT COUNT(*) FROM ptax_daily").fetchone()[0] == 1
    finally:
        connection.close()

    bronze_file = next((data_root / "bronze" / "source=focus").rglob("*.json"))
    bronze_document = json.loads(bronze_file.read_text(encoding="utf-8"))
    assert bronze_document["record_count"] == 4
    assert bronze_document["source"] == "focus"
    assert bronze_document["request"] == {
        "data_final": "2026-10-20",
        "data_inicial": "2026-10-20",
    }
    assert len(bronze_document["payload_sha256"]) == 64


def test_pipeline_preserves_previous_focus_when_api_fails(tmp_path: Path, monkeypatch) -> None:
    _configure_stubs(monkeypatch)
    data_root = tmp_path / "data"
    run_pipeline(_config(data_root))
    focus_path = data_root / "silver" / "focus" / "focus.parquet"
    before = focus_path.read_bytes()

    OlindaExtractorStub.fail_focus = True
    try:
        result = run_pipeline(_config(data_root))
    finally:
        OlindaExtractorStub.fail_focus = False

    assert result["failed_sources"] == ["focus"]
    assert result["focus_rows"] == 4
    assert focus_path.read_bytes() == before


def test_cli_exits_with_error_when_pipeline_is_partial(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline",
            "--data-root",
            str(tmp_path / "data"),
            "--log-dir",
            str(tmp_path / "logs"),
        ],
    )
    monkeypatch.setattr(
        "src.pipelines.run.run_pipeline",
        lambda config: {
            "end_date": "2026-10-20",
            "sgs_rows": 1,
            "focus_rows": 1,
            "ptax_rows": 1,
            "silver_changed": False,
            "gold_rebuilt": False,
            "failed_sources": ["focus"],
        },
    )

    with pytest.raises(SystemExit) as error:
        main()

    assert error.value.code == 2
