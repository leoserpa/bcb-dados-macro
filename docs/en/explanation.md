# Architecture explanation

Conceptual overview of how Bronze, Silver, Gold, and Evidence.dev fit together and why those boundaries exist. Concrete trade-offs and rejected alternatives are recorded in [docs/decisions/](../decisions/README.md).

## End-to-end flow overview

```mermaid
flowchart TB
    subgraph SRC["Public Sources — Central Bank of Brazil"]
        SGS(["SGS API<br/>17 macro series"])
        FOCUS(["Olinda Focus<br/>Annual Expectations"])
        TOP5(["Olinda Focus Top 5<br/>Short · Medium · Long"])
        PTAX(["Olinda PTAX<br/>USD · EUR Bulletins"])
    end

    subgraph BRZ_L["Bronze Layer · data/bronze/"]
        BRZ[("Immutable JSON Snapshots<br/>SHA-256 Hash · Metadata · Atomic Write")]
    end

    ETL["Validation & Idempotent Upsert<br/>Strict Pydantic v2 · Polars · 7d Lookback"]

    subgraph SLV_L["Silver Layer · data/silver/ (ZSTD Parquet)"]
        S_SGS[("sgs.parquet<br/>PK: data, codigo_serie")]
        S_FOC[("focus.parquet<br/>PK: 5 columns")]
        S_T5[("focus_top5.parquet<br/>PK: 4 columns")]
        S_PTAX[("ptax.parquet<br/>PK: time, currency, bulletin")]
    end

    subgraph GLD_L["Gold Layer · data/gold/ (Atomic Rebuild)"]
        DUCK[("bcb_macro.duckdb<br/>7 tables + 6 analytical views<br/>CHECKPOINT + .replace")]
    end

    subgraph OUT_L["Export, Quality & Serving"]
        GPARQ[("Gold ZSTD Parquets<br/>macro_indicators · ptax_daily")]
        QUAL{{"Quality Gate<br/>src.pipelines.quality<br/>Schema · PK · 17 SGS · Staleness"}}
        EVID(["Evidence.dev + DuckDB-WASM<br/>7 pages · build:strict · GitHub Pages"])
    end

    SGS & FOCUS & TOP5 & PTAX --> BRZ
    BRZ --> ETL
    ETL --> S_SGS & S_FOC & S_T5 & S_PTAX
    S_SGS & S_FOC & S_T5 & S_PTAX --> DUCK
    DUCK --> GPARQ
    DUCK --> QUAL
    DUCK --> EVID

    classDef source fill:#1c1f26,stroke:#525252,stroke-width:1.5px,color:#f5f5f5
    classDef bronze fill:#261a10,stroke:#c27803,stroke-width:1.5px,color:#f5f5f5
    classDef transform fill:#161616,stroke:#737373,stroke-width:1.5px,stroke-dasharray:4 3,color:#e5e5e5
    classDef silver fill:#161b22,stroke:#94a3b8,stroke-width:1.5px,color:#f5f5f5
    classDef gold fill:#291507,stroke:#ff6b00,stroke-width:2.5px,color:#ffffff,font-weight:bold
    classDef quality fill:#161616,stroke:#a6a6a6,stroke-width:1.5px,color:#f5f5f5
    classDef serving fill:#ff6b00,stroke:#ff8533,stroke-width:2px,color:#0f0f0f,font-weight:bold

    class SGS,FOCUS,TOP5,PTAX source
    class BRZ bronze
    class ETL transform
    class S_SGS,S_FOC,S_T5,S_PTAX silver
    class DUCK gold
    class GPARQ silver
    class QUAL quality
    class EVID serving

    style SRC fill:transparent,stroke:#404040,stroke-dasharray:3 3
    style BRZ_L fill:transparent,stroke:#404040,stroke-dasharray:3 3
    style SLV_L fill:transparent,stroke:#404040,stroke-dasharray:3 3
    style GLD_L fill:transparent,stroke:#ff6b00,stroke-dasharray:3 3
    style OUT_L fill:transparent,stroke:#404040,stroke-dasharray:3 3
```

## Why use the Medallion Architecture?

The **Bronze** layer stores raw JSON responses from BCB APIs alongside request parameters and a deterministic SHA-256 checksum. **Silver** enforces Pydantic v2 contracts (`extra="forbid"`), parses Brazilian numeric formatting (decimal commas, `"-"`, `"nan"`) into `Float64`, normalizes ISO/UTC dates, and writes deduplicated ZSTD Parquet datasets. **Gold** reads solely from Silver to materialize analytical tables, window metrics, and SQL views in DuckDB.

This separation allows transformations and analytical models to evolve and rebuild cleanly without re-querying historical API ranges ([ADR-001](../decisions/ADR-001-medallion-polars-duckdb-rebuild-atomico.md)).

## How do idempotency and lookback work?

```mermaid
flowchart LR
    START(["Scheduled Run<br/>Mon–Fri 09:30 BRT"]) --> LOOK["7d Lookback<br/>per series & currency"]
    LOOK --> FETCH{"BCB API<br/>responded?"}
    FETCH -->|"Yes"| UPSERT["Silver Upsert<br/>(content changed?)"]
    FETCH -->|"HTTP/JSON Error"| KEEP["Preserve Silver<br/>+ failed_sources"]
    UPSERT -->|"Yes"| GOLD["Atomic Gold Rebuild<br/>+ Quality Gate"]
    UPSERT -->|"No"| SKIP["Keep current Gold<br/>(zero diff)"]
    KEEP --> EXIT2(["Exit code 2<br/>partial run"])
    GOLD --> PAGES(["Deploy GitHub Pages<br/>build:strict"])

    classDef source fill:#1c1f26,stroke:#525252,stroke-width:1.5px,color:#f5f5f5
    classDef transform fill:#161616,stroke:#737373,stroke-width:1.5px,color:#e5e5e5
    classDef gold fill:#291507,stroke:#ff6b00,stroke-width:2px,color:#ffffff,font-weight:bold
    classDef serving fill:#ff6b00,stroke:#ff8533,stroke-width:2px,color:#0f0f0f,font-weight:bold
    classDef warn fill:#261a10,stroke:#c27803,stroke-width:1.5px,color:#f5f5f5

    class START,SKIP source
    class LOOK,FETCH,UPSERT transform
    class KEEP,EXIT2 warn
    class GOLD gold
    class PAGES serving
```

Daily runs neither re-download all history since `2010-01-01` nor assume BCB series never revise recent observations:

- Without `--start-date`, the orchestrator looks back `7` days (`--lookback-days`) from the latest persisted date per SGS series and PTAX currency.
- During Silver consolidation, `upsert_parquet` first deduplicates all business columns keeping the **earliest** `ingested_at`, and then deduplicates on primary key keeping the latest observation.

Late BCB revisions overwrite stale numbers, while unchanged re-fetches keep original timestamps and avoid noisy binary commits in Git ([ADR-002](../decisions/ADR-002-ingestao-incremental-lookback-e-falha-parcial.md)).

## Why rebuild Gold atomically?

Gold combines base copies (`sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`) with full-history window computations (`ptax_risk_metrics`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_repricing`, `vw_focus_top5_vs_geral`). Instead of patching a live database file with incremental DML, `build_gold` constructs `bcb_macro.tmp.duckdb`, runs `CHECKPOINT`, closes the connection, and atomically swaps files only when Silver changes or Gold is missing ([ADR-001](../decisions/ADR-001-medallion-polars-duckdb-rebuild-atomico.md)).

## How are reliability and partial failures handled?

- **HTTP transport:** `30s` timeout and 3 exponential retries (`2s`, `4s`, `8s`) on `429` and `5xx`, plus `3650`-day chunking on SGS queries.
- **Per-source isolation:** if an SGS series, Focus, Focus Top 5, or a PTAX currency fails, `failed_sources` records it, prior Silver data remains untouched, healthy sources still commit to Silver, and the CLI exits with status `2` ([ADR-002](../decisions/ADR-002-ingestao-incremental-lookback-e-falha-parcial.md)).
- **Quality gate and test suite:** `src.pipelines.quality` verifies core schemas, non-nulls, PK uniqueness, all 17 SGS series, all 4 Focus indicators, row counts, and staleness bounds; Pytest enforces `>= 85%` coverage.

## Why Evidence.dev and DuckDB-WASM?

Compiling the dashboard with **Evidence.dev** turns the SQL sources under `reports/sources/bcb_macro/` and `bcb_macro.duckdb` into a static site backed by DuckDB-WASM in the browser, requiring zero runtime backend servers ([ADR-003](../decisions/ADR-003-evidence-static-bi-e-duckdb-wasm.md)). The UI uses neutral dark surfaces with `#ff6b00` as a single focal accent, direct endpoint series labels, and pure typographic conditional formatting ([ADR-004](../decisions/ADR-004-gramatica-visual-editorial-e-formatacao-tipografica.md)).

Versão em português: [Explicação da arquitetura](../pt/explanation.md).
