# How-to guides

Task-focused recipes for incremental runs, analytical SQL queries, dashboard builds, and failure recovery.

## Run an incremental load

```bash
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

The pipeline re-fetches the latest seven days per SGS series and PTAX currency to capture late BCB revisions.

## Run a historical load or targeted backfill

```bash
uv run python -m src.pipelines.run \
  --start-date 2010-01-01 \
  --end-date 2026-11-25 \
  --currency USD,EUR \
  --log-dir logs
```

To test additional PTAX currencies locally, pass comma-separated codes via `--currency` (for example, `USD,EUR,GBP`).

## Query real interest rates and monetary stance

```sql
SELECT
    data,
    selic_meta,
    ipca_focus_ano,
    juro_real_ex_ante,
    regime_monetario
FROM vw_macro_regime
ORDER BY data DESC
LIMIT 15;
```

To inspect the monthly series comparing ex-ante and ex-post real rates:

```sql
SELECT *
FROM vw_juro_real_completo
ORDER BY data DESC
LIMIT 24;
```

## Compare Focus Top 5 against general consensus

```sql
SELECT
    indicador,
    data_referencia,
    tipo_calculo,
    mediana_top5,
    mediana_geral,
    spread_top5_vs_geral
FROM vw_focus_top5_vs_geral
WHERE indicador = 'IPCA'
ORDER BY data_referencia, tipo_calculo;
```

In `focus_expectations`, `mediana` represents market expectations for the horizon in `data_referencia`, not realized values.

## Read Parquet files directly with DuckDB

```sql
SELECT * FROM 'data/silver/sgs/sgs.parquet' LIMIT 10;
SELECT * FROM 'data/gold/ptax_daily.parquet' ORDER BY data_referencia DESC LIMIT 10;
```

## Build and strictly validate the Evidence dashboard

Whenever `data/gold/bcb_macro.duckdb` or files under `reports/` change:

```bash
cd reports
npm ci
npm run sources
npm run build:strict
```

Run `npm run build:strict` before committing to verify all 11 SQL sources and 7 Markdown pages compile without errors.

## Troubleshoot a failure

1. Inspect structured JSON entries in `logs/pipeline.log`.
2. Check `failed_sources` in the JSON summary printed to stdout (for example `"sgs:24364"`, `"focus_top5"`, or `"ptax:EUR"`).
3. Re-run the quality gate:

```bash
uv run python -m src.pipelines.quality \
  --database data/gold/bcb_macro.duckdb \
  --max-staleness-days 10
```

4. On partial failure, existing Silver datasets for failing sources are preserved and the process exits with code `2`. Retry once upstream BCB endpoints recover.

## Run via GitHub Actions

- **Data pipeline:** open **Actions → BCB Data Pipeline → Run workflow** and optionally set `start_date`, `end_date`, and `lookback_days`. Scheduled runs trigger Monday–Friday at `12:30 UTC` (`09:30 BRT`).
- **Dashboard deployment:** open **Actions → Deploy Evidence Dashboard → Run workflow**, or let it trigger automatically on pushes to `reports/**` or `data/gold/**` or after a successful `BCB Data Pipeline` run.

Versão em português: [Guias práticos](../pt/how-to.md).
