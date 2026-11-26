# Technical reference

Exact specification for CLI commands, flags, BCB endpoints, Silver primary keys, Gold tables and views, quality checks, Evidence dashboard assets, and workflows.

## Commands

### Python pipeline (`uv`)

| Task | Command |
|---|---|
| Install dependencies | `uv sync --frozen --dev` |
| Lint | `uv run ruff check .` |
| Check formatting | `uv run ruff format --check .` |
| Run tests and coverage | `uv run pytest --cov=src --cov-fail-under=85 -q` |
| Run ingestion | `uv run python -m src.pipelines.run` |
| Validate Gold quality | `uv run python -m src.pipelines.quality` |

> On hosts where Python 3.14 is not installed yet, pass `--frozen --python 3.12` after `uv run`. The module path `python -m src.pipeline.run` forwards to `src.pipelines.run`.

### Evidence dashboard (`reports/`)

| Script (`npm run <script>`) | Action |
|---|---|
| `sync-db` | Copies `../data/gold/bcb_macro.duckdb` to `reports/sources/bcb_macro/bcb_macro.duckdb` |
| `sources` | Runs `sync-db` and builds the 11 SQL sources (`evidence sources`) |
| `sources:strict` | Runs `sync-db` and `evidence sources --strict` |
| `dev` | Runs `sync-db` and launches dev server at `/bcb-dados-macro` |
| `build` | Compiles static site into `reports/build/` |
| `build:strict` | Compiles strictly, failing on any SQL or component error |
| `preview` | Serves the built static site locally |

## Command-line options

### `src.pipelines.run`

| Option | Type | Default | Description |
|---|---|---|---|
| `--start-date` | `YYYY-MM-DD` | `None` (uses lookback/initial date) | Overrides extraction start date |
| `--end-date` | `YYYY-MM-DD` | Today in `America/Sao_Paulo` | Extraction end date |
| `--lookback-days` | `int` | `7` | Days re-fetched prior to max persisted date |
| `--currency` | `str` | `"USD,EUR"` | Comma-separated PTAX currencies |
| `--data-root` | `Path` | `data/` | Root directory for Bronze/Silver/Gold layers |
| `--log-dir` | `Path` | `logs/` | Output directory for `pipeline.log` |

- **Note:** Direct Python calls constructing `PipelineConfig` without `currency` default to `"USD"`, whereas the CLI parser defaults `--currency` to `"USD,EUR"`.
- **Exit codes:** `0` on full completion; `2` on partial failure (healthy sources update normally while failed sources keep their prior Silver dataset).

### `src.pipelines.quality`

| Option | Type | Default | Description |
|---|---|---|---|
| `--database` | `Path` | `data/gold/bcb_macro.duckdb` | DuckDB file path to validate |
| `--as-of-date` | `YYYY-MM-DD` | Today in `America/Sao_Paulo` | Reference date for future-date and staleness checks |
| `--max-staleness-days` | `int` | `None` | Maximum allowed age in days for SGS, Focus, and PTAX |

- **Exit code:** `0` when `passed = true`; `1` when any critical check fails.

## Configured sources

### SGS (`src/extractors/sgs.py`) — 17 series

Queried via `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados` in chunks of up to `3650` days (`max_span_days`). HTTP `404` responses and JSON payloads `{"erro": {"statusCode": 404}}` on empty windows are logged and skipped cleanly.

| Code | Series name | Frequency |
|---|---|---|
| `11` | Taxa Selic diária | `diaria` |
| `189` | IGP-M variação mensal | `mensal` |
| `432` | Meta Selic definida pelo Copom | `evento` |
| `433` | IPCA variação mensal | `mensal` |
| `4513` | DLSP/PIB | `mensal` |
| `5793` | Resultado primário 12m/PIB | `mensal` |
| `13522` | IPCA acumulado 12 meses | `mensal` |
| `13762` | DBGG/PIB | `mensal` |
| `13967` | Fluxo cambial comercial | `diaria` |
| `13970` | Fluxo cambial financeiro | `diaria` |
| `13982` | Reservas internacionais | `diaria` |
| `20631` | Concessões totais de crédito | `mensal` |
| `20714` | Taxa média de juros de crédito | `mensal` |
| `20783` | Spread médio do crédito | `mensal` |
| `21082` | Inadimplência total do SFN | `mensal` |
| `24364` | IBC-Br com ajuste sazonal | `mensal` |
| `24369` | Taxa de desocupação (PNAD) | `mensal` |

### Olinda (`src/extractors/olinda.py`)

OData pagination with `page_size = 1000` following `@odata.nextLink`, `$skip` offset fallback, and loop detection (`visited_urls`).

| Source | Olinda endpoint | Configured scope |
|---|---|---|
| Focus | `Expectativas/versao/v1/odata/ExpectativasMercadoAnuais` | Indicators `IPCA`, `Selic`, `Câmbio`, `PIB Total` |
| Focus Top 5 | `Expectativas/versao/v1/odata/ExpectativasMercadoTop5Anuais` | Indicators `IPCA`, `Selic`, `Câmbio`, `PIB Total` (`tipoCalculo`: `C`, `M`, `L`) |
| PTAX | `PTAX/versao/v1/odata/CotacaoMoedaPeriodo(...)` | Intraday bulletins for `--currency` (`USD,EUR` on CLI) |

## Bronze and Silver layers

- **Bronze (`src/utils/storage.py`):** immutable JSON snapshots at `data/bronze/source=<source>/ingestion_date=YYYY-MM-DD/<file>__<sha256[:16]>.json` storing canonical SHA-256 checksums and request metadata.
- **Silver (`src/models/schemas.py`, `src/transformers/medallion.py`):** Pydantic v2 contracts (`extra="forbid"`) written to Parquet with ZSTD compression and statistics. Upserts preserve the earliest `ingested_at` when business columns are identical and keep the latest record per key when values change.

| Silver dataset | File | Primary key | Normalization / filter |
|---|---|---|---|
| SGS | `data/silver/sgs/sgs.parquet` | `data`, `codigo_serie` | `retain_rows` restricts rows to codes in `SGS_SERIES` |
| Focus | `data/silver/focus/focus.parquet` | `data`, `indicador`, `data_referencia`, `indicador_detalhe`, `base_calculo` | Null `indicador_detalhe` → `""`; null `base_calculo` → `-1` |
| Focus Top 5 | `data/silver/focus_top5/focus_top5.parquet` | `data`, `indicador`, `data_referencia`, `tipo_calculo` | `tipo_calculo` trimmed via `.strip()` |
| PTAX | `data/silver/ptax/ptax.parquet` | `data_hora_cotacao`, `moeda`, `tipo_boletim` | `data_referencia` derived from `data_hora_cotacao` if omitted |

## Gold layer (`src/pipelines/gold.py`)

Atomically rebuilt via temporary files (`bcb_macro.tmp.duckdb`, `*.tmp.parquet`), `CHECKPOINT`, connection close, and atomic `replace()`.

### Tables (7)

| Table | Description |
|---|---|
| `sgs_series` | Typed copy of all 17 series from `sgs.parquet` |
| `focus_expectations` | Annual market expectations from `focus.parquet` |
| `focus_top5` | Top 5 annual projections from `focus_top5.parquet` |
| `ptax_quotes` | All intraday PTAX bulletins from `ptax.parquet` |
| `macro_indicators` | Long-format union of `sgs_series` (`fonte='SGS'`) and `focus_expectations` (`fonte='FOCUS'`) |
| `ptax_daily` | One priority daily rate per `(data_referencia, moeda)`, preferring `tipo_boletim = 'Fechamento'` then latest timestamp |
| `ptax_risk_metrics` | Spread (`cotacao_venda - cotacao_compra`), `retorno_diario_pct`, `media_movel_21d`, `media_movel_252d`, `vol_anualizada_21d` (`STDDEV_SAMP(log_return) * SQRT(252) * 100`), and `zscore_252d` |

### Views (6)

| View | Core definition |
|---|---|
| `vw_macro_latest` | Latest `data_observacao` per `fonte`, `indicador_id`, horizon (empty for SGS), `metrica`, and `detalhe` |
| `vw_focus_repricing` | Compares latest `base_calculo = 0` (30d) median against `base_calculo = 1` (5 business days), computing `repricing_b1_vs_b0` and `drift_30d` via `LAG(mediana, 21)` |
| `vw_macro_regime` | Joins SGS `432` with current-year `IPCA` Focus median (`base_calculo = 0`); computes Fisher ex-ante real rate `((1 + selic_meta/100) / (1 + ipca_focus_ano/100) - 1) * 100`, classifying `>= 6.0` as `Restritivo`, `>= 3.5` as `Neutro`, and `< 3.5` as `Expansionista` |
| `vw_juro_real_completo` | Monthly series joining Selic Target (`432`), 12m IPCA (`13522`), and `vw_macro_regime` to expose `juro_real_ex_post` and `juro_real_ex_ante`, using explicit `CAST(date_trunc('month', data) AS DATE)` |
| `vw_focus_top5_vs_geral` | Latest `focus_top5` median per `(indicador, data_referencia, tipo_calculo)` against general consensus (`base_calculo = 0`), computing `spread_top5_vs_geral` |
| `vw_lakehouse_lineage` | Row counts, `data_minima`, `data_maxima`, and `ultima_ingestao` across `sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`, `ptax_daily`, and `macro_indicators` |

### Gold Parquet exports

- `data/gold/macro_indicators.parquet` (ZSTD)
- `data/gold/ptax_daily.parquet` (ZSTD)

## Quality checks (`src/pipelines/quality.py`)

The quality gate runs critical assertions against `bcb_macro.duckdb`:

- **Required objects (`EXPECTED_TABLES`):** `sgs_series`, `focus_expectations`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `vw_macro_latest`.
- **Schema and non-nulls:** required columns and zero nulls on core fields in `sgs_series`, `focus_expectations`, and `ptax_quotes`.
- **Non-empty tables and PK uniqueness:** verifies zero duplicate primary keys in SGS, Focus, and PTAX.
- **Domain and finiteness:** verifies all 17 series in `EXPECTED_SGS_SERIES`, all 4 indicators in `EXPECTED_FOCUS_INDICATORS`, and `isfinite()` on numeric columns.
- **Row reconciliation:** `COUNT(macro_indicators) == COUNT(sgs_series) + COUNT(focus_expectations)` and `0 < COUNT(ptax_daily) <= COUNT(ptax_quotes)`.
- **Dates and freshness:** rejects dates later than `--as-of-date` and optionally enforces `--max-staleness-days`.

> **Known scope:** `focus_top5`, `ptax_risk_metrics`, and the 5 analytical views (`vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral`, `vw_lakehouse_lineage`) are not in `quality.py`'s `EXPECTED_TABLES`; they are validated when Gold rebuilds and when Evidence runs `npm run sources && npm run build:strict`.

## Evidence dashboard (`reports/`)

- **Base path:** `/bcb-dados-macro` (`reports/evidence.config.yaml`)
- **Core packages:** `@evidence-dev/evidence` `^40.1.8`, `@evidence-dev/core-components` `^5.4.2`, `@evidence-dev/duckdb` `^2.0.1`, `typescript` `^5.8.3`
- **Pages (`reports/pages/`):**
  - `/` (`index.md`) — Panorama
  - `/inteligencia-de-mercado` (`inteligencia-de-mercado.md`) — Inteligência de Mercado & Simulador
  - `/juros-e-atividade` (`juros-e-atividade.md`) — Juros & Atividade
  - `/inflacao-e-trabalho` (`inflacao-e-trabalho.md`) — Inflação & Trabalho
  - `/cambio` (`cambio.md`) — Câmbio & Setor Externo
  - `/focus` (`focus.md`) — Expectativas Focus
  - `/qualidade-e-linhagem` (`qualidade-e-linhagem.md`) — Qualidade & Linhagem
- **SQL sources (`reports/sources/bcb_macro/`):** 11 queries mirroring `sgs_series`, `focus_expectations`, `focus_top5`, `ptax_daily`, `ptax_risk_metrics`, `vw_macro_latest`, `vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral`, and `vw_lakehouse_lineage`.
- **Custom Svelte components (`reports/components/`):** `KPITerminalCard.svelte`, `ExecutiveTable.svelte`, `ConditionalTable.svelte`, `TerminalLineChart.svelte`, `FilterBar.svelte`.

## Network, logging, and CI/CD

- **HTTP client (`src/utils/http_client.py`):** `30s` default timeout; `ExponentialRetry` with `total=3` (`connect=3`, `read=3`, `status=3`) on `GET` for `429, 500, 502, 503, 504`, `2s`, `4s`, `8s` waits, and connection pool size `10`.
- **Logging (`src/utils/logging_config.py`):** one JSON object per line to console and `logs/pipeline.log` via `RotatingFileHandler` (`5 MiB` max, `5` backups).
- **Environment and Python:** `BCB_INITIAL_DATE` overrides the default start date (`2010-01-01`). `pyproject.toml` sets `requires-python = ">=3.11"`; `.python-version` and CI use Python `3.14`.
- **Workflows (`.github/workflows/`):**
  - `data_pipeline.yml`: Monday–Friday at `12:30 UTC` (`09:30 BRT`) or manual; runs Ruff, Pytest (`--cov-fail-under=85`), ingestion, quality gate (`--max-staleness-days 10`), and commits `data/` on changes.
  - `deploy_pages.yml`: runs on pushes to `data/gold/**` or `reports/**`, after `BCB Data Pipeline` succeeds, or manual dispatch; runs `npm run sources && npm run build:strict` on Node 20 and deploys to GitHub Pages.
  - `codeql.yml`: scans `python` and `actions` on pushes/PRs to `main` and Mondays at `14:00 UTC`.

Versão em português: [Referência técnica](../pt/reference.md).
