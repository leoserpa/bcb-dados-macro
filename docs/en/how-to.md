# How-to guides

## Run an incremental load

```powershell
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

The pipeline reprocesses the latest seven days to capture late BCB revisions.

## Run a historical load

```powershell
uv run python -m src.pipelines.run `
  --start-date 2010-01-01 `
  --end-date 2026-10-21 `
  --currency USD `
  --log-dir logs
```

## Query Focus Selic expectations

```sql
SELECT data, data_referencia, mediana, media, base_calculo
FROM focus_expectations
WHERE indicador = 'Selic'
ORDER BY data DESC, data_referencia
LIMIT 20;
```

`mediana` is a market expectation for the period in `data_referencia`; it is not the current Copom decision. Historical values such as 7.0 or 6.5 may be valid forecasts for different reference years.

## Read a Parquet file with SQL

```sql
SELECT * FROM 'data/silver/sgs/sgs.parquet' LIMIT 10;
```

## Troubleshoot a failure

1. Check `logs/pipeline.log`.
2. Inspect `failed_sources` in the JSON summary.
3. Run the quality gate again.
4. If a source is unavailable, previous Silver data is preserved. A partial run exits with code `2`.
5. Retry when the BCB API is available.

## Run through GitHub Actions

Open **Actions → BCB Data Pipeline → Run workflow** and optionally provide `start_date`, `end_date`, and `lookback_days`. Scheduled runs execute Monday through Friday at 12:30 UTC (09:30 BRT).

Portuguese version: [Guias práticos](../pt/how-to.md).
