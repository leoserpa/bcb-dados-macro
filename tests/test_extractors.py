from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from src.extractors.olinda import FOCUS_URL, OlindaExtractor
from src.extractors.sgs import ExtractionError, SGSExtractor


class ResponseStub:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self.payload


class SessionStub:
    def __init__(self, responses: list[ResponseStub]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> ResponseStub:
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


class InvalidJSONResponseStub(ResponseStub):
    headers = {"Content-Type": "text/html"}

    def json(self) -> Any:
        raise requests.exceptions.JSONDecodeError("resposta vazia", "", 0)


def test_sgs_extractor_formats_incremental_dates() -> None:
    session = SessionStub([ResponseStub([{"data": "20/10/2026", "valor": "14.90"}])])
    extractor = SGSExtractor(session)

    result = extractor.fetch_series(11, date(2026, 10, 1), date(2026, 10, 20))

    assert result == [{"data": "20/10/2026", "valor": "14.90"}]
    assert session.calls[0]["params"] == {
        "formato": "json",
        "dataInicial": "01/10/2026",
        "dataFinal": "20/10/2026",
    }
    assert session.calls[0]["timeout"] == 30


def test_sgs_extractor_splits_long_periods() -> None:
    session = SessionStub([ResponseStub([]), ResponseStub([]), ResponseStub([])])
    extractor = SGSExtractor(session, max_span_days=2)

    extractor.fetch_series(11, date(2026, 1, 1), date(2026, 1, 5))

    assert [call["params"]["dataInicial"] for call in session.calls] == [
        "01/01/2026",
        "03/01/2026",
        "05/01/2026",
    ]


def test_sgs_extractor_treats_missing_period_as_empty() -> None:
    session = SessionStub([ResponseStub({}, status_code=404)])
    extractor = SGSExtractor(session)

    result = extractor.fetch_series(24364, date(2026, 10, 1), date(2026, 10, 20))

    assert result == []


def test_sgs_extractor_treats_embedded_not_found_error_as_empty() -> None:
    session = SessionStub(
        [
            ResponseStub(
                {
                    "erro": {
                        "statusCode": 404,
                        "detail": "SGSNegocioException: Value(s) not found",
                    }
                }
            )
        ]
    )
    extractor = SGSExtractor(session)

    result = extractor.fetch_series(13967, date(2026, 10, 21), date(2026, 10, 21))

    assert result == []


def test_sgs_extractor_reports_embedded_api_error() -> None:
    session = SessionStub([ResponseStub({"erro": {"statusCode": 500, "detail": "falha interna"}})])
    extractor = SGSExtractor(session)

    with pytest.raises(ExtractionError, match="falha interna"):
        extractor.fetch_series(13967, date(2026, 10, 20), date(2026, 10, 21))


def test_sgs_extractor_reports_non_json_response() -> None:
    session = SessionStub([InvalidJSONResponseStub(None)])
    extractor = SGSExtractor(session)

    with pytest.raises(ExtractionError, match="SGS 11 retornou resposta não JSON"):
        extractor.fetch_series(11, date(2025, 1, 1), date(2025, 1, 3))


def test_focus_extractor_follows_odata_next_link() -> None:
    next_link = f"{FOCUS_URL}?$skip=1"
    session = SessionStub(
        [
            ResponseStub(
                {
                    "value": [{"Indicador": "IPCA", "Data": "2026-10-10"}],
                    "@odata.nextLink": next_link,
                }
            ),
            ResponseStub({"value": [{"Indicador": "IPCA", "Data": "2026-10-09"}]}),
        ]
    )
    extractor = OlindaExtractor(session, page_size=2)

    result = extractor.fetch_focus(date(2026, 10, 1), date(2026, 10, 20), indicators=("IPCA",))

    assert result == [
        {"Indicador": "IPCA", "Data": "2026-10-10"},
        {"Indicador": "IPCA", "Data": "2026-10-09"},
    ]
    first_url = session.calls[0]["url"]
    first_query = parse_qs(urlparse(first_url).query)
    assert first_query["$filter"] == [
        "(Indicador eq 'IPCA') and Data ge '2026-10-01' and Data le '2026-10-20'"
    ]
    assert "$orderby" in first_query
    assert "%20" in first_url
    assert "+" not in first_url
    assert session.calls[1]["url"] == next_link


def test_focus_extractor_uses_skip_when_api_omits_next_link() -> None:
    session = SessionStub(
        [
            ResponseStub(
                {
                    "value": [
                        {"Indicador": "IPCA", "Data": "2026-10-10"},
                        {"Indicador": "IPCA", "Data": "2026-10-09"},
                    ]
                }
            ),
            ResponseStub({"value": [{"Indicador": "IPCA", "Data": "2026-10-08"}]}),
        ]
    )
    extractor = OlindaExtractor(session, page_size=2)

    result = extractor.fetch_focus(indicators=("IPCA",))

    assert len(result) == 3
    second_query = parse_qs(urlparse(session.calls[1]["url"]).query)
    assert second_query["$skip"] == ["2"]


def test_ptax_extractor_formats_odata_function_parameters() -> None:
    session = SessionStub([ResponseStub({"value": []})])
    extractor = OlindaExtractor(session)

    extractor.fetch_ptax(date(2026, 10, 1), date(2026, 10, 20), "usd")

    params = parse_qs(urlparse(session.calls[0]["url"]).query)
    assert params["@moeda"] == ["'USD'"]
    assert params["@dataInicial"] == ["'10-01-2026'"]
    assert params["@dataFinalCotacao"] == ["'10-20-2026'"]
    assert "$orderby" not in params


def test_olinda_rejects_invalid_payload() -> None:
    session = SessionStub([ResponseStub({"unexpected": []})])
    extractor = OlindaExtractor(session)

    with pytest.raises(ExtractionError, match="Payload OData inesperado"):
        extractor.fetch_focus()


@pytest.mark.parametrize("max_span_days", [0, -1])
def test_sgs_rejects_invalid_window_size(max_span_days: int) -> None:
    with pytest.raises(ValueError, match="max_span_days"):
        SGSExtractor(SessionStub([]), max_span_days=max_span_days)


@pytest.mark.parametrize("page_size", [0, -1])
def test_olinda_rejects_invalid_page_size(page_size: int) -> None:
    with pytest.raises(ValueError, match="page_size"):
        OlindaExtractor(SessionStub([]), page_size=page_size)


@pytest.mark.parametrize("extractor", [SGSExtractor, OlindaExtractor])
def test_extractors_reject_non_positive_timeout(extractor) -> None:
    with pytest.raises(ValueError, match="timeout"):
        extractor(SessionStub([]), timeout=0)
