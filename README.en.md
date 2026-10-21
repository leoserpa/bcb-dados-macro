# BCB Macro Lakehouse

A batch, incremental, and idempotent pipeline for collecting public macroeconomic data from the Central Bank of Brazil (BCB). The project uses Python 3.11+, Polars, DuckDB, Requests, Pydantic v2, Ruff, and Pytest with the Medallion Architecture.

**Português:** [Leia este documento em português](README.md).

## Quick start

Requirements: Windows PowerShell and `uv`.

```powershell
uv python install 3.14
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python -m src.pipelines.run
```

Validate the generated database:

```powershell
uv run python -m src.pipelines.quality `
  --database data\gold\bcb_macro.duckdb `
  --max-staleness-days 10
```

## Architecture

```text
BCB SGS + Olinda
       |
       v
Bronze: immutable raw JSON snapshots
       |
       v
Silver: typed, deduplicated, validated Parquet
       |
       v
Gold: analytical DuckDB tables and views + Parquet
```

Bronze snapshots are identified by their SHA-256 hash and store request metadata. Silver uses explicit keys and idempotent upserts. Gold is rebuilt when Silver data changes.

## Data sources

- **SGS:** nine time series, including Selic, IBC-Br, international reserves, credit, and DBGG/GDP.
- **Focus:** annual market expectations for IPCA, Selic, exchange rates, and total GDP, with OData pagination.
- **PTAX:** USD quotations; Gold prioritizes the daily closing bulletin.

HTTP requests use a 30-second timeout and retry status codes 429, 500, 502, 503, and 504 with 2, 4, and 8-second backoff.

## Layers and tables

| Layer | Location | Contents |
|---|---|---|
| Bronze | `data/bronze/` | Raw JSON snapshots |
| Silver | `data/silver/` | Typed Parquet datasets |
| Gold | `data/gold/bcb_macro.duckdb` | Analytical tables and views |

Gold tables: `sgs_series`, `focus_expectations`, `ptax_quotes`, `ptax_daily`, `macro_indicators`, and `vw_macro_latest`.

## Loads

The first load starts at `2010-01-01` by default. Later runs use the latest persisted date minus seven days to capture late revisions.

Historical load:

```powershell
uv run python -m src.pipelines.run `
  --start-date 2010-01-01 `
  --end-date YYYY-MM-DD `
  --log-dir logs
```

Incremental load:

```powershell
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

Replace `YYYY-MM-DD` with the desired end date.

## Automation and logs

The `.github/workflows/data_pipeline.yml` workflow runs Monday through Friday at 12:30 UTC (09:30 BRT) and supports manual runs. It runs Ruff, Pytest, ingestion, and validation, then versions `data/` only when files change. Logs are written to `logs/pipeline.log`.

If a source fails, previous Silver data is preserved and the pipeline exits with code `2` to report a partial run.

## Documentation

- [Documentation in English](docs/en/README.md)
- [Documentação em português](docs/pt/README.md)
- [Bilingual documentation index](docs/README.md)
