# BCB Macro Lakehouse

Pipeline batch, incremental e idempotente para coletar dados macroeconômicos públicos do Banco Central do Brasil (BCB). O projeto usa Python 3.11+, Polars, DuckDB, Requests, Pydantic v2, Ruff e Pytest, com arquitetura Medallion.

**English:** [Read this document in English](README.en.md).

## Início rápido

Requisitos: Windows PowerShell e `uv`.

```powershell
uv python install 3.14
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python -m src.pipelines.run
```

Valide a base gerada:

```powershell
uv run python -m src.pipelines.quality `
  --database data\gold\bcb_macro.duckdb `
  --max-staleness-days 10
```

## Arquitetura

```text
BCB SGS + Olinda
       |
       v
Bronze: snapshots JSON brutos e imutáveis
       |
       v
Silver: Parquet tipado, deduplicado e validado
       |
       v
Gold: tabelas e visões analíticas DuckDB + Parquet
```

Snapshots Bronze são identificados pelo hash SHA-256 e guardam os metadados da requisição. A camada Silver usa chaves explícitas e upsert idempotente. A Gold é reconstruída quando os dados Silver mudam.

## Fontes de dados

- **SGS:** nove séries, incluindo Selic, IBC-Br, reservas, crédito e DBGG/PIB.
- **Focus:** expectativas anuais de IPCA, Selic, Câmbio e PIB Total, com paginação OData.
- **PTAX:** cotações de USD; a Gold prioriza o boletim de fechamento diário.

As requisições HTTP usam timeout de 30 segundos e retries para erros 429, 500, 502, 503 e 504, com espera de 2, 4 e 8 segundos.

## Camadas e tabelas

| Camada | Localização | Conteúdo |
|---|---|---|
| Bronze | `data/bronze/` | Snapshots JSON brutos |
| Silver | `data/silver/` | Conjuntos Parquet tipados |
| Gold | `data/gold/bcb_macro.duckdb` | Tabelas e visões analíticas |

Tabelas Gold: `sgs_series`, `focus_expectations`, `ptax_quotes`, `ptax_daily`, `macro_indicators` e `vw_macro_latest`.

## Cargas

A primeira carga começa em `2010-01-01` por padrão. As execuções seguintes usam a maior data persistida menos sete dias para capturar revisões tardias.

Carga histórica:

```powershell
uv run python -m src.pipelines.run `
  --start-date 2010-01-01 `
  --end-date AAAA-MM-DD `
  --log-dir logs
```

Carga incremental:

```powershell
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

Substitua `AAAA-MM-DD` pela data final desejada no formato `YYYY-MM-DD`.

## Automação e logs

O workflow `.github/workflows/data_pipeline.yml` roda de segunda a sexta às 12:30 UTC (09:30 BRT) e também aceita execução manual. Ele executa Ruff, Pytest, ingestão e validação; versiona `data/` somente quando há mudanças. Os logs ficam em `logs/pipeline.log`.

Se uma fonte falhar, os dados Silver anteriores são preservados e o pipeline termina com código `2`, indicando uma execução parcial.

## Documentação

- [Documentação em português](docs/pt/README.md)
- [Documentation in English](docs/en/README.md)
- [Índice bilíngue](docs/README.md)
