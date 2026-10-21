"""Extractors for Focus expectations and PTAX on BCB Olinda."""

from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote, urlencode, urljoin

import requests

from src.extractors.sgs import ExtractionError
from src.utils.http_client import DEFAULT_TIMEOUT_SECONDS

FOCUS_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoAnuais"
)
PTAX_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,"
    "dataFinalCotacao=@dataFinalCotacao)"
)
FOCUS_INDICATORS = ("IPCA", "Selic", "C" + "\u00e2" + "mbio", "PIB Total")


class OlindaExtractor:
    """Fetch paginated OData resources from BCB Olinda."""

    def __init__(
        self,
        session: requests.Session,
        *,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        page_size: int = 1000,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout deve ser maior que zero")
        if page_size <= 0:
            raise ValueError("page_size deve ser maior que zero")
        self.session = session
        self.timeout = min(timeout, DEFAULT_TIMEOUT_SECONDS)
        self.page_size = page_size

    def fetch_focus(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        indicators: tuple[str, ...] = FOCUS_INDICATORS,
    ) -> list[dict[str, Any]]:
        """Fetch annual Focus expectations for the configured indicators."""
        escaped_indicators = (indicator.replace("'", "''") for indicator in indicators)
        indicator_filter = " or ".join(
            f"Indicador eq '{indicator}'" for indicator in escaped_indicators
        )
        filters = [f"({indicator_filter})"]
        if start_date is not None:
            filters.append(f"Data ge '{start_date.isoformat()}'")
        if end_date is not None:
            filters.append(f"Data le '{end_date.isoformat()}'")

        params = {
            "$filter": " and ".join(filters),
            "$orderby": "Data desc",
            "$select": (
                "Indicador,IndicadorDetalhe,Data,DataReferencia,Media,Mediana,"
                "DesvioPadrao,Minimo,Maximo,numeroRespondentes,baseCalculo"
            ),
            "$top": str(self.page_size),
            "$format": "json",
        }
        return self._fetch_paginated(FOCUS_URL, params)

    def fetch_ptax(
        self,
        start_date: date,
        end_date: date,
        currency: str = "USD",
    ) -> list[dict[str, Any]]:
        """Fetch all PTAX bulletins for a currency and date interval."""
        if start_date > end_date:
            raise ValueError("start_date deve ser menor ou igual a end_date")
        params = {
            "@moeda": f"'{currency.upper()}'",
            "@dataInicial": f"'{start_date.strftime('%m-%d-%Y')}'",
            "@dataFinalCotacao": f"'{end_date.strftime('%m-%d-%Y')}'",
            "$select": (
                "paridadeCompra,paridadeVenda,cotacaoCompra,cotacaoVenda,"
                "dataHoraCotacao,tipoBoletim"
            ),
            "$top": str(self.page_size),
            "$format": "json",
        }
        return self._fetch_paginated(PTAX_URL, params)

    def _fetch_paginated(self, url: str, params: dict[str, str]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        next_url: str | None = url
        next_params: dict[str, str] | None = params
        visited_urls: set[str] = set()
        offset = int(params.get("$skip", "0"))

        while next_url is not None:
            request_url = self._url_with_params(next_url, next_params)
            if request_url in visited_urls:
                raise ExtractionError("Loop detectado na paginação OData")
            visited_urls.add(request_url)

            response = self.session.get(request_url, timeout=self.timeout)
            response.raise_for_status()
            try:
                payload = response.json()
            except requests.exceptions.JSONDecodeError as error:
                status_code = getattr(response, "status_code", "desconhecido")
                content_type = getattr(response, "headers", {}).get("Content-Type", "desconhecido")
                raise ExtractionError(
                    "Olinda retornou resposta não JSON "
                    f"(status={status_code}, content_type={content_type})"
                ) from error
            if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
                raise ExtractionError("Payload OData inesperado")
            page = payload["value"]
            records.extend(page)

            raw_next_link = payload.get("@odata.nextLink")
            if raw_next_link:
                next_url = urljoin(request_url, raw_next_link)
                next_params = None
            elif len(page) == self.page_size:
                offset += len(page)
                next_url = url
                next_params = {**params, "$skip": str(offset)}
            else:
                next_url = None
                next_params = None

        return records

    @staticmethod
    def _url_with_params(url: str, params: dict[str, str] | None) -> str:
        if not params:
            return url
        separator = "&" if "?" in url else "?"
        query = urlencode(params, quote_via=quote)
        return f"{url}{separator}{query}"
