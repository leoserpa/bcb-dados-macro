# Explicação da arquitetura

Visão conceitual de como Bronze, Silver, Gold e Evidence.dev trabalham juntos e por que essas fronteiras existem. Os trade-offs e alternativas rejeitadas estão detalhados em [docs/decisions/](../decisions/README.md).

## Visão geral do fluxo

```mermaid
flowchart TB
    subgraph SRC["Fontes Públicas — Banco Central do Brasil"]
        SGS(["SGS API<br/>17 séries macro"])
        FOCUS(["Olinda Focus<br/>Expectativas Anuais"])
        TOP5(["Olinda Focus Top 5<br/>Curto · Médio · Longo"])
        PTAX(["Olinda PTAX<br/>Boletins USD · EUR"])
    end

    subgraph BRZ_L["Camada Bronze · data/bronze/"]
        BRZ[("Snapshots JSON Imutáveis<br/>Hash SHA-256 · Metadados · Escrita atômica")]
    end

    ETL["Validação & Upsert Idempotente<br/>Pydantic v2 estrito · Polars · Lookback 7d"]

    subgraph SLV_L["Camada Silver · data/silver/ (Parquet ZSTD)"]
        S_SGS[("sgs.parquet<br/>PK: data, codigo_serie")]
        S_FOC[("focus.parquet<br/>PK: 5 colunas")]
        S_T5[("focus_top5.parquet<br/>PK: 4 colunas")]
        S_PTAX[("ptax.parquet<br/>PK: hora, moeda, boletim")]
    end

    subgraph GLD_L["Camada Gold · data/gold/ (Rebuild Atômico)"]
        DUCK[("bcb_macro.duckdb<br/>7 tabelas + 6 views analíticas<br/>CHECKPOINT + .replace")]
    end

    subgraph OUT_L["Exportação, Qualidade & Consumo"]
        GPARQ[("Parquets Gold ZSTD<br/>macro_indicators · ptax_daily")]
        QUAL{{"Quality Gate<br/>src.pipelines.quality<br/>Schema · PK · 17 SGS · Staleness"}}
        EVID(["Evidence.dev + DuckDB-WASM<br/>7 páginas · build:strict · GitHub Pages"])
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

## Por que usar a arquitetura Medallion?

A camada **Bronze** preserva o payload JSON bruto retornado pelas APIs do BCB junto com os parâmetros da requisição e um hash SHA-256 determinístico. A **Silver** impõe contratos Pydantic v2 (`extra="forbid"`), converte strings numéricas brasileiras (vírgula decimal, `"-"`, `"nan"`) para `Float64`, normaliza datas em UTC/ISO e grava arquivos Parquet ZSTD deduplicados por chave primária. A **Gold** lê apenas a Silver para materializar tabelas analíticas, métricas derivadas e views SQL no DuckDB.

Essa separação permite reprocessar regras de transformação e reconstruir a Gold sem refazer centenas de requisições históricas nas APIs do BCB ([ADR-001](../decisions/ADR-001-medallion-polars-duckdb-rebuild-atomico.md)).

## Como funcionam a idempotência e o lookback?

```mermaid
flowchart LR
    START(["Execução Diária<br/>Seg–Sex 09:30 BRT"]) --> LOOK["Lookback 7d<br/>por série e moeda"]
    LOOK --> FETCH{"API BCB<br/>respondeu?"}
    FETCH -->|"Sim"| UPSERT["Upsert Silver<br/>(conteúdo mudou?)"]
    FETCH -->|"Erro HTTP/JSON"| KEEP["Preserva Silver<br/>+ failed_sources"]
    UPSERT -->|"Sim"| GOLD["Rebuild Atômico Gold<br/>+ Quality Gate"]
    UPSERT -->|"Não"| SKIP["Mantém Gold atual<br/>(zero diff)"]
    KEEP --> EXIT2(["Exit code 2<br/>execução parcial"])
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

Execuções diárias não baixam todo o histórico desde `2010-01-01` nem dependem de um corte seco sem tolerância a correções:

- Sem `--start-date`, o orquestrador retrocede `7` dias (`--lookback-days`) a partir da maior data persistida por série SGS ou moeda PTAX.
- Ao consolidar na Silver, `upsert_parquet` primeiro deduplica todas as colunas de negócio mantendo o **menor** `ingested_at` e depois deduplica pela chave primária mantendo o registro mais recente.

Assim, revisões tardias do BCB substituem valores antigos, enquanto reconsultas idênticas preservam os hashes e timestamps originais e evitam commits binários sem mudança real de dados ([ADR-002](../decisions/ADR-002-ingestao-incremental-lookback-e-falha-parcial.md)).

## Por que rebuild atômico da Gold?

A camada Gold mistura tabelas diretas (`sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`) com agregações e funções de janela sobre toda a série histórica (`ptax_risk_metrics`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_repricing`, `vw_focus_top5_vs_geral`). Em vez de aplicar `INSERT`/`UPDATE` parciais no banco ativo, `build_gold` constrói `bcb_macro.tmp.duckdb`, executa `CHECKPOINT`, fecha a conexão e substitui os arquivos finais atomicamente somente quando a Silver mudou ou o banco não existe ([ADR-001](../decisions/ADR-001-medallion-polars-duckdb-rebuild-atomico.md)).

## Como confiabilidade e falhas parciais são tratadas?

- **Transporte HTTP:** timeout de `30s` e 3 tentativas com espera fixa de `2s`, `4s` e `8s` em erros transitórios (`429`, `5xx`), além de janelas de no máximo `3650` dias no SGS.
- **Isolamento por fonte:** se uma série SGS, o Focus, o Focus Top 5 ou uma moeda PTAX falhar, `failed_sources` registra o item, o Parquet Silver anterior é mantido íntegro, fontes saudáveis avançam e o CLI encerra com código `2` ([ADR-002](../decisions/ADR-002-ingestao-incremental-lookback-e-falha-parcial.md)).
- **Portão de qualidade e testes:** `src.pipelines.quality` verifica schema, nulos, chaves únicas, as 17 séries SGS, os 4 indicadores Focus, reconciliação de linhas e defasagem máxima; a suíte Pytest exige cobertura mínima de `85%`.

## Por que Evidence.dev + DuckDB-WASM?

Publicar o dashboard em **Evidence.dev** compila as consultas SQL de `reports/sources/bcb_macro/` diretamente sobre `bcb_macro.duckdb` em ativos estáticos executados via DuckDB-WASM no navegador, eliminando servidores Python pagos ou bancos externos ([ADR-003](../decisions/ADR-003-evidence-static-bi-e-duckdb-wasm.md)). A interface segue uma paleta escura neutra com foco único em `#ff6b00`, rótulos diretos nas séries finais e formatação condicional puramente tipográfica ([ADR-004](../decisions/ADR-004-gramatica-visual-editorial-e-formatacao-tipografica.md)).

English version: [Architecture explanation](../en/explanation.md).
