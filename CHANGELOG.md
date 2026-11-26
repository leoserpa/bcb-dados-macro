# Changelog

Todas as mudanças relevantes deste projeto estão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- Registros de Decisão Arquitetural ([ADR-001](docs/decisions/ADR-001-medallion-polars-duckdb-rebuild-atomico.md) a [ADR-004](docs/decisions/ADR-004-gramatica-visual-editorial-e-formatacao-tipografica.md)) e índice em [docs/decisions/README.md](docs/decisions/README.md).
- Guia de convenções e restrições operacionais do repositório em [AGENTS.md](AGENTS.md).
- Este arquivo [CHANGELOG.md](CHANGELOG.md).

### Alterado
- Sincronizada a documentação principal ([README.md](README.md), [README.en.md](README.en.md)) e a documentação bilíngue ([docs/pt/](docs/pt/README.md), [docs/en/](docs/en/README.md)) com as 17 séries SGS, Focus Top 5, PTAX `USD,EUR`, os 13 objetos Gold e o dashboard Evidence de 7 páginas.

## [0.1.0] - 2026-11-25

### Adicionado
- Pipeline Medallion completo em Python (`src/extractors/`, `src/models/`, `src/transformers/`, `src/pipelines/`, `src/utils/`) com Python 3.11+, Polars, DuckDB, Pydantic v2, Requests, Ruff e Pytest.
- Armazenamento Bronze em JSON imutável endereçado por SHA-256 (`data/bronze/`), camada Silver em Parquet ZSTD validada por contratos Pydantic (`extra="forbid"`) e camada Gold com rebuild atômico (`bcb_macro.tmp.duckdb` + `CHECKPOINT` + `.replace()`).
- Expansão do catálogo SGS de 9 para 17 séries (`11`, `189`, `432`, `433`, `4513`, `5793`, `13522`, `13762`, `13967`, `13970`, `13982`, `20631`, `20714`, `20783`, `21082`, `24364`, `24369`).
- Extração do Boletim Focus Top 5 (`ExpectativasMercadoTop5Anuais`) em `data/silver/focus_top5/focus_top5.parquet` e suporte multi-moeda na PTAX (`--currency USD,EUR` por padrão na CLI).
- Tabelas e views analíticas adicionais na Gold: `focus_top5`, `ptax_risk_metrics`, `vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral` e `vw_lakehouse_lineage`.
- Portão de qualidade determinístico (`python -m src.pipelines.quality`) validando esquema, não nulidade, unicidade de chave primária, séries SGS, indicadores Focus, finitude numérica, reconciliação de contagens e janela de atualização (`--max-staleness-days`).
- Dashboard estático em Evidence.dev (`reports/`) com 7 páginas (`Panorama`, `Inteligência`, `Juros`, `Inflação`, `Câmbio`, `Focus`, `Linhagem`), 11 consultas SQL e 4 componentes Svelte customizados (`KPITerminalCard`, `ExecutiveTable`, `ConditionalTable`, `TerminalLineChart`).
- Layout editorial escuro (`#0f0f0f`/`#161616`) com destaque único em `#ff6b00`, menu mobile em ícone único com `popover="auto"`, formatação condicional tipográfica em 3 níveis, rótulos diretos de série final em gráficos de linha, barras divergentes no resultado primário e unidades sensíveis à linha/indicador nas tabelas (`%`, `pp`, `R$`, `$`).
- Automação via GitHub Actions: ingestão diária em dias úteis (`data_pipeline.yml`), build estrito e deploy no GitHub Pages (`deploy_pages.yml`), análise CodeQL (`codeql.yml`), configuração CodeRabbit (`.coderabbit.yaml`) e licença `GPL-3.0-only`.

### Corrigido
- Conversão explícita `CAST(date_trunc('month', data) AS DATE)` em `vw_juro_real_completo` para compatibilidade de binder `DATE` com Evidence/DuckDB-WASM e ativação de `npm run build:strict`.
- Fixação de `typescript` `^5.8.3` em `reports/package.json` para instalar dependências do Evidence/SvelteKit sem `--legacy-peer-deps`.
- Remoção de fundo interno escuro em gráficos ECharts nos painéis e ajuste de razão entre colunas de gráfico e tabela.
- Exibição dinâmica de unidades (`%` ou `R$`) nos cartões KPI e gráficos do Focus, remoção de `.0` em códigos inteiros do SGS, prevenção de truncamento nos subtítulos dos cartões KPI e ajuste de padding/`yMax` no gráfico de linhagem para evitar corte do rótulo líder.
