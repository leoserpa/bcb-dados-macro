"""Pydantic v2 data contracts for the Silver layer."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _parse_nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid numeric value")
    if isinstance(value, int | float):
        return float(value)

    normalized = str(value).strip()
    if normalized.lower() in {"", "nan", "null", "none", "-"}:
        return None
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    return float(normalized)


class ContractModel(BaseModel):
    """Shared strict contract behavior for upstream records."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SGSRecord(ContractModel):
    """Normalized observation from Sistema Gerenciador de Séries Temporais."""

    data: date
    codigo_serie: int
    nome_serie: str
    frequencia: str
    valor: float | None
    ingested_at: datetime

    @field_validator("data", mode="before")
    @classmethod
    def parse_brazilian_date(cls, value: Any) -> Any:
        if isinstance(value, str) and "/" in value:
            return datetime.strptime(value, "%d/%m/%Y").date()
        return value

    @field_validator("valor", mode="before")
    @classmethod
    def parse_value(cls, value: Any) -> float | None:
        return _parse_nullable_float(value)


class FocusRecord(ContractModel):
    """Normalized annual market expectation from the Focus survey."""

    indicador: str = Field(alias="Indicador")
    indicador_detalhe: str | None = Field(default=None, alias="IndicadorDetalhe")
    data: date = Field(alias="Data")
    data_referencia: str = Field(alias="DataReferencia")
    media: float | None = Field(default=None, alias="Media")
    mediana: float | None = Field(default=None, alias="Mediana")
    desvio_padrao: float | None = Field(default=None, alias="DesvioPadrao")
    minimo: float | None = Field(default=None, alias="Minimo")
    maximo: float | None = Field(default=None, alias="Maximo")
    numero_respondentes: int | None = Field(default=None, alias="numeroRespondentes")
    base_calculo: int | None = Field(default=None, alias="baseCalculo")
    ingested_at: datetime

    @field_validator("data", mode="before")
    @classmethod
    def parse_iso_date(cls, value: Any) -> Any:
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        return value

    @field_validator("data_referencia", mode="before")
    @classmethod
    def normalize_reference(cls, value: Any) -> str:
        return str(value).strip()

    @field_validator("media", "mediana", "desvio_padrao", "minimo", "maximo", mode="before")
    @classmethod
    def parse_statistics(cls, value: Any) -> float | None:
        return _parse_nullable_float(value)


class PTAXRecord(ContractModel):
    """Normalized exchange-rate bulletin from the PTAX service."""

    moeda: str
    data_hora_cotacao: datetime = Field(alias="dataHoraCotacao")
    data_referencia: date | None = None
    cotacao_compra: float | None = Field(default=None, alias="cotacaoCompra")
    cotacao_venda: float | None = Field(default=None, alias="cotacaoVenda")
    paridade_compra: float | None = Field(default=None, alias="paridadeCompra")
    paridade_venda: float | None = Field(default=None, alias="paridadeVenda")
    tipo_boletim: str = Field(alias="tipoBoletim")
    ingested_at: datetime

    @field_validator(
        "cotacao_compra",
        "cotacao_venda",
        "paridade_compra",
        "paridade_venda",
        mode="before",
    )
    @classmethod
    def parse_quotes(cls, value: Any) -> float | None:
        return _parse_nullable_float(value)

    @model_validator(mode="after")
    def derive_reference_date(self) -> PTAXRecord:
        if self.data_referencia is None:
            self.data_referencia = self.data_hora_cotacao.date()
        return self
