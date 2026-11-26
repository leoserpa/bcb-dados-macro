# Changelog

Todas as mudanças relevantes deste projeto estão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [0.1.0] - 2026-11-25

### Adicionado
- Pipeline Medallion completo em Python (`src/extractors/`, `src/models/`, `src/transformers/`, `src/pipelines/`, `src/utils/`) com Python 3.11+, Polars, DuckDB, Pydantic v2, Requests, Ruff e Pytest.
- Armazenamento Bronze em JSON imutável endereçado por SHA-256 (`data/bronze/`), camada Silver em Parquet ZSTD validada por contratos Pydantic (`extra="forbid"`) e camada Gold com rebuild atômico (`bcb_macro.tmp.duckdb` + `CHECKPOINT` + `.replace()`).
- Catálogo SGS com 17 séries (`11`, `189`, `432`, `433`, `4513`, `5793`, `13522`, `13762`, `13967`, `13970`, `13982`, `20631`, `20714`, `20783`, `21082`, `24364`, `24369`), Focus anual (`ExpectativasMercadoAnuais`), Focus Top 5 (`ExpectativasMercadoTop5Anuais`) e PTAX multi-moeda (`--currency USD,EUR` por padrão na CLI).
- 7 tabelas e 6 views analíticas na camada Gold (`sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `ptax_risk_metrics`, `vw_macro_latest`, `vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral`, `vw_lakehouse_lineage`) e 2 exportações Parquet ZSTD.
- Portão de qualidade determinístico (`python -m src.pipelines.quality`) validando esquema, não nulidade, unicidade de chave primária, as 17 séries SGS, os 4 indicadores Focus, finitude numérica, reconciliação de contagens e janela de atualização (`--max-staleness-days`).
- Dashboard estático em Evidence.dev (`reports/`) com 7 páginas (`Panorama`, `Inteligência`, `Juros`, `Inflação`, `Câmbio`, `Focus`, `Linhagem`), 11 consultas SQL e 4 componentes Svelte customizados (`KPITerminalCard`, `ExecutiveTable`, `ConditionalTable`, `TerminalLineChart`).
- Layout editorial escuro (`#0f0f0f`/`#161616`) com destaque único em `#ff6b00`, menu mobile em ícone único com `popover="auto"`, formatação condicional tipográfica em 3 níveis, rótulos diretos de série final em gráficos de linha, barras divergentes no resultado primário e escalonamento em bilhões para Reservas Internacionais (`US$ bi`), Concessões de Crédito (`R$ bi`) e Fluxo Cambial Mensal (`US$ bi`).
- Automação via GitHub Actions: ingestão diária em dias úteis (`data_pipeline.yml`), build estrito (`npm run build:strict`) e deploy no GitHub Pages (`deploy_pages.yml`), análise CodeQL (`codeql.yml`), configuração CodeRabbit (`.coderabbit.yaml`) e licença `GPL-3.0-only`.
- Documentação bilíngue Diátaxis ([docs/pt/](docs/pt/README.md), [docs/en/](docs/en/README.md)) com fluxogramas Mermaid, Registros de Decisão Arquitetural ([ADR-001](docs/decisions/ADR-001-medallion-polars-duckdb-rebuild-atomico.md) a [ADR-004](docs/decisions/ADR-004-gramatica-visual-editorial-e-formatacao-tipografica.md)) e guia operacional ([AGENTS.md](AGENTS.md)).

### Corrigido
- Conversão explícita `CAST(date_trunc('month', data) AS DATE)` em `vw_juro_real_completo` para compatibilidade de binder `DATE` com Evidence/DuckDB-WASM e ativação de `npm run build:strict`.
- Fixação de `typescript` `^5.8.3` em `reports/package.json` para instalar dependências do Evidence/SvelteKit sem `--legacy-peer-deps`.
- Remoção de fundo interno escuro em gráficos ECharts nos painéis, ajuste de razão entre colunas de gráfico e tabela, prevenção de truncamento nos subtítulos KPI e ajuste de padding/`yMax` no gráfico horizontal de linhagem.
- Exibição dinâmica de unidades (`%`, `pp`, `R$`, `US$`), posicionamento do sinal negativo antes do prefixo monetário (`-US$ 1.279 mi`) e remoção de `.0` em códigos inteiros do SGS.

[Não lançado]: https://github.com/leoserpa/bcb-dados-macro/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/leoserpa/bcb-dados-macro/releases/tag/v0.1.0
