"""Extractor for the BCB Sistema Gerenciador de Séries Temporais API."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import requests

from src.utils.http_client import DEFAULT_TIMEOUT_SECONDS

SGS_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SeriesDefinition:
    code: int
    name: str
    frequency: str


SGS_SERIES: dict[int, SeriesDefinition] = {
    11: SeriesDefinition(11, "Taxa Selic diária", "diaria"),
    432: SeriesDefinition(432, "Meta Selic definida pelo Copom", "evento"),
    24364: SeriesDefinition(24364, "IBC-Br com ajuste sazonal", "mensal"),
    13967: SeriesDefinition(13967, "Fluxo cambial comercial", "diaria"),
    13970: SeriesDefinition(13970, "Fluxo cambial financeiro", "diaria"),
    13982: SeriesDefinition(13982, "Reservas internacionais", "diaria"),
    21082: SeriesDefinition(21082, "Inadimplência total do SFN", "mensal"),
    20631: SeriesDefinition(20631, "Concessões totais de crédito", "mensal"),
    13762: SeriesDefinition(13762, "DBGG/PIB", "mensal"),
}


class ExtractionError(RuntimeError):
    """Raised when an upstream API returns an invalid payload."""


class SGSExtractor:
    """Fetch SGS observations with bounded date windows."""

    def __init__(
        self,
        session: requests.Session,
        *,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_span_days: int = 3650,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout deve ser maior que zero")
        if max_span_days <= 0:
            raise ValueError("max_span_days deve ser maior que zero")
        self.session = session
        self.timeout = min(timeout, DEFAULT_TIMEOUT_SECONDS)
        self.max_span_days = max_span_days

    def fetch_series(
        self,
        code: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch one SGS series, splitting long histories into safe windows."""
        if code not in SGS_SERIES:
            raise ValueError(f"Série SGS não configurada: {code}")
        if (start_date is None) != (end_date is None):
            raise ValueError("start_date e end_date devem ser informadas juntas")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("start_date deve ser menor ou igual a end_date")

        periods: Iterator[tuple[date | None, date | None]]
        if start_date is None or end_date is None:
            periods = iter([(None, None)])
        else:
            periods = self._iter_periods(start_date, end_date)

        records: list[dict[str, Any]] = []
        for period_start, period_end in periods:
            params: dict[str, str] = {"formato": "json"}
            if period_start is not None and period_end is not None:
                params.update(
                    {
                        "dataInicial": period_start.strftime("%d/%m/%Y"),
                        "dataFinal": period_end.strftime("%d/%m/%Y"),
                    }
                )
            response = self.session.get(
                SGS_BASE_URL.format(code=code),
                params=params,
                timeout=self.timeout,
            )
            if getattr(response, "status_code", None) == 404:
                LOGGER.warning(
                    "SGS %s não possui dados no intervalo %s a %s",
                    code,
                    period_start or "completo",
                    period_end or "atual",
                )
                continue
            response.raise_for_status()
            try:
                payload = response.json()
            except requests.exceptions.JSONDecodeError as error:
                status_code = getattr(response, "status_code", "desconhecido")
                content_type = getattr(response, "headers", {}).get("Content-Type", "desconhecido")
                raise ExtractionError(
                    f"SGS {code} retornou resposta não JSON "
                    f"(status={status_code}, content_type={content_type})"
                ) from error
            if isinstance(payload, dict) and "erro" in payload:
                error_payload = payload["erro"]
                if isinstance(error_payload, dict) and error_payload.get("statusCode") == 404:
                    LOGGER.warning(
                        "SGS %s não possui dados no intervalo %s a %s",
                        code,
                        period_start or "completo",
                        period_end or "atual",
                    )
                    continue
                detail = error_payload.get("detail") if isinstance(error_payload, dict) else None
                raise ExtractionError(f"SGS {code} retornou erro: {detail or error_payload}")
            if not isinstance(payload, list):
                raise ExtractionError(f"Payload inesperado para a série SGS {code}")
            records.extend(payload)
        return records

    def _iter_periods(self, start_date: date, end_date: date) -> Iterator[tuple[date, date]]:
        current_start = start_date
        while current_start <= end_date:
            current_end = min(
                current_start + timedelta(days=self.max_span_days - 1),
                end_date,
            )
            yield current_start, current_end
            current_start = current_end + timedelta(days=1)
