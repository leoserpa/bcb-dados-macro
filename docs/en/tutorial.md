# Tutorial: first run

This tutorial takes you from environment setup to a validated Gold database.

## 1. Set up the environment

From the repository root in PowerShell:

```powershell
uv python install 3.14
uv sync --dev
```

## 2. Check the code

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

## 3. Download the historical data

```powershell
uv run python -m src.pipelines.run `
  --start-date 2010-01-01 `
  --end-date 2026-10-21 `
  --log-dir logs
```

Replace `2026-10-21` with the desired end date. The run writes Bronze snapshots, updates Silver Parquet files, and rebuilds Gold when the data changes.

## 4. Validate the data

```powershell
uv run python -m src.pipelines.quality `
  --database data\gold\bcb_macro.duckdb `
  --as-of-date 2026-10-21 `
  --max-staleness-days 10
```

The `passed` field should be `true`.

## 5. Query the tables

```powershell
uv run python -c "import duckdb; c=duckdb.connect('data/gold/bcb_macro.duckdb'); print(c.sql('SHOW TABLES'))"
```

Portuguese version: [Tutorial: primeira execução](../pt/tutorial.md).
