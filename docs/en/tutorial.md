# Tutorial: first run

This tutorial guides you from environment setup to a validated Gold database and a running local dashboard.

## 1. Set up the environment

From the repository root (Linux/macOS shell; PowerShell equivalents work identically):

```bash
uv python install 3.14
uv sync --frozen --dev
```

> If your local host only has Python 3.12 installed, pass `--frozen --python 3.12` after `uv run` in the steps below.

## 2. Check code quality and tests

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=src --cov-fail-under=85 -q
```

## 3. Download the historical dataset

```bash
uv run python -m src.pipelines.run \
  --start-date 2010-01-01 \
  --end-date 2026-11-25 \
  --currency USD,EUR \
  --log-dir logs
```

Replace `2026-11-25` with your target date (`YYYY-MM-DD`). This run writes Bronze JSON snapshots, updates the 4 Silver Parquet datasets, and builds `data/gold/bcb_macro.duckdb` alongside `macro_indicators.parquet` and `ptax_daily.parquet`.

## 4. Validate data quality

```bash
uv run python -m src.pipelines.quality \
  --database data/gold/bcb_macro.duckdb \
  --as-of-date 2026-11-25 \
  --max-staleness-days 10
```

The JSON output field `passed` should be `true`.

## 5. Query the Gold database

```bash
uv run python -c "import duckdb; c=duckdb.connect('data/gold/bcb_macro.duckdb'); print(c.sql('SHOW ALL TABLES'))"
```

This lists all 7 tables (`sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `ptax_risk_metrics`) and 6 analytical views.

## 6. Start the Evidence dashboard locally (optional)

Requires Node.js 18+ (Node 20 recommended):

```bash
cd reports
npm install
npm run sources
npm run dev
```

The local server opens at `http://localhost:3000/bcb-dados-macro`.

Versão em português: [Tutorial: primeira execução](../pt/tutorial.md).
