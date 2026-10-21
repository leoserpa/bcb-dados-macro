# Technical reference

## Commands

| Task | Command |
|---|---|
| Install dependencies | `uv sync --dev` |
| Lint | `uv run ruff check .` |
| Check formatting | `uv run ruff format --check .` |
| Run tests | `uv run pytest -q` |
| Run ingestion | `uv run python -m src.pipelines.run` |
| Validate quality | `uv run python -m src.pipelines.quality` |

## Command-line options

`src.pipelines.run` accepts `--start-date`, `--end-date`, `--lookback-days`, `--currency`, `--data-root`, and `--log-dir`. Dates use `YYYY-MM-DD`; the default currency is `USD`.

`src.pipelines.quality` accepts `--database`, `--as-of-date`, and `--max-staleness-days`.

## Configured sources

- **SGS:** series `11`, `432`, `13762`, `13967`, `13970`, `13982`, `20631`, `21082`, and `24364`.
- **Focus:** indicators `IPCA`, `Selic`, `Câmbio`, and `PIB Total`.
- **PTAX:** USD quotations.

## Idempotency keys

| Dataset | Key |
|---|---|
| SGS | `data`, `codigo_serie` |
| Focus | `data`, `indicador`, `data_referencia`, `indicador_detalhe`, `base_calculo` |
| PTAX | `data_hora_cotacao`, `moeda`, `tipo_boletim` |

## Gold tables

- `sgs_series`: typed SGS observations.
- `focus_expectations`: annual market expectations.
- `ptax_quotes`: PTAX quotation bulletins.
- `ptax_daily`: one priority daily quotation per currency.
- `macro_indicators`: observed values and Focus medians in long format.
- `vw_macro_latest`: latest observation by indicator, reference period, and metric.

## Quality checks

The quality gate checks required tables and columns, non-empty datasets, nulls, key uniqueness, expected domains, finite numeric values, Gold reconciliation, future dates, and source freshness.

## Configuration

`BCB_INITIAL_DATE` changes the default initial date. The project requires Python `>=3.11`; the development environment uses Python 3.14.

Versão em português: [Referência técnica](../pt/reference.md).
