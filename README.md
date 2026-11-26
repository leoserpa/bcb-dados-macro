# BCB Macro Lakehouse

Pipeline incremental e idempotente para coletar séries macroeconômicas públicas do Banco Central do Brasil (BCB), persistir camadas Bronze/Silver/Gold e publicar um dashboard analítico estático em Evidence.dev. Usa Python 3.11+, Polars, DuckDB, Pydantic v2, Requests, Ruff e Pytest.

- **Dashboard ao vivo:** <https://leoserpa.github.io/bcb-dados-macro/>
- **English:** [Read this document in English](README.en.md)

## Início rápido

Requisitos: `uv` (Python 3.11+ recomendado; `.python-version` fixa `3.14` no CI) e Node.js 18+ caso queira compilar o dashboard em `reports/`.

Em Linux/macOS (ou Windows PowerShell equivalente):

```bash
uv sync --frozen --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=src --cov-fail-under=85 -q
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

Valide a base Gold gerada:

```bash
uv run python -m src.pipelines.quality \
  --database data/gold/bcb_macro.duckdb \
  --max-staleness-days 10
```

> **Nota de ambiente local:** se o host ainda não tiver Python 3.14 instalado, adicione `--frozen --python 3.12` aos comandos `uv run` (por exemplo, `uv run --frozen --python 3.12 pytest -q`).

## Arquitetura

```text
BCB SGS (17 séries) + Olinda (Focus, Focus Top 5, PTAX)
        |
        v
Bronze (data/bronze/): snapshots JSON imutáveis endereçados por SHA-256
        |
        v
Silver (data/silver/): 4 arquivos Parquet ZSTD tipados (Pydantic v2 + Polars)
        |
        v
Gold (data/gold/bcb_macro.duckdb + 2 Parquets): rebuild atômico (7 tabelas + 6 views)
        |
        v
Dashboard (reports/): Evidence.dev + DuckDB-WASM -> GitHub Pages
```

Cada execução grava snapshots Bronze com hash SHA-256 e metadados da requisição, aplica upsert idempotente na Silver preservando `ingested_at` quando não há alteração nos valores de negócio e reconstrói a Gold atomicamente (`bcb_macro.tmp.duckdb` + `CHECKPOINT` + `.replace()`) apenas quando a Silver muda ou o banco Gold não existe. Consulte as justificativas de arquitetura em [docs/decisions/](docs/decisions/README.md).

## Fontes de dados

- **SGS (`src/extractors/sgs.py`):** 17 séries cobrindo juros e liquidez (`11`, `432`), inflação (`189`, `433`, `13522`), atividade e emprego (`24364`, `24369`), crédito (`20631`, `20714`, `20783`, `21082`), contas públicas (`4513`, `5793`, `13762`) e setor externo (`13967`, `13970`, `13982`), fatiadas em janelas de até `3650` dias.
- **Focus (`ExpectativasMercadoAnuais`):** expectativas anuais de `IPCA`, `Selic`, `Câmbio` e `PIB Total`, com paginação OData (`page_size = 1000`).
- **Focus Top 5 (`ExpectativasMercadoTop5Anuais`):** projeções anuais dos grupos de curto, médio e longo prazo (`tipoCalculo`: `C`, `M`, `L`) para os mesmos 4 indicadores.
- **PTAX (`CotacaoMoedaPeriodo`):** boletins intradia para `USD,EUR` por padrão na CLI (`--currency`); a tabela `ptax_daily` prioriza o boletim `Fechamento` (ou o último horário disponível).

As requisições HTTP utilizam timeout de `30s` e 3 tentativas exponenciais (`2s`, `4s`, `8s`) para códigos `429`, `500`, `502`, `503` e `504`.

## Camadas e ativos Gold

| Camada | Localização | Conteúdo |
|---|---|---|
| Bronze | `data/bronze/source=*/ingestion_date=*/` | Snapshots JSON brutos + SHA-256 |
| Silver | `data/silver/{sgs,focus,focus_top5,ptax}/` | 4 datasets Parquet ZSTD deduplicados |
| Gold | `data/gold/bcb_macro.duckdb` | 7 tabelas + 6 views analíticas |
| Gold Parquet | `data/gold/{macro_indicators,ptax_daily}.parquet` | Cópias ZSTD exportadas da Gold |

**Tabelas Gold (7):** `sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `ptax_risk_metrics`.

**Views Gold (6):** `vw_macro_latest`, `vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral`, `vw_lakehouse_lineage`.

## Cargas e tolerância a falhas

A primeira carga começa em `2010-01-01` (`BCB_INITIAL_DATE`). Execuções incrementais consultam a maior data persistida por série ou moeda menos `7` dias (`--lookback-days`) para capturar revisões tardias do BCB.

Carga histórica completa ou parcial:

```bash
uv run python -m src.pipelines.run \
  --start-date 2010-01-01 \
  --end-date 2026-11-25 \
  --currency USD,EUR \
  --log-dir logs
```

Carga incremental diária:

```bash
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

Se uma fonte falhar, os dados Silver anteriores dela são preservados, o erro entra em `failed_sources` e o processo retorna código `2` (execução parcial).

## Dashboard (Evidence.dev + GitHub Pages)

O diretório `reports/` publica um terminal analítico estático em **Evidence.dev** com 7 páginas (`Panorama`, `Inteligência`, `Juros`, `Inflação`, `Câmbio`, `Focus` e `Linhagem`), 11 consultas SQL em `reports/sources/bcb_macro/` e 4 componentes Svelte customizados (`KPITerminalCard`, `ExecutiveTable`, `ConditionalTable`, `TerminalLineChart`).

Para rodar ou validar localmente (Node.js 20+ recomendado):

```bash
cd reports
npm ci
npm run sources
npm run build:strict
npm run dev
```

## Automação, qualidade e segurança

- **`.github/workflows/data_pipeline.yml`:** executa de segunda a sexta às `12:30 UTC` (`09:30 BRT`) ou sob demanda (`workflow_dispatch`). Roda Ruff, Pytest (`--cov-fail-under=85`), ingestão e quality gate (`--max-staleness-days 10`), fazendo commit em `data/` apenas quando há mudança real nos dados. Logs ficam em `logs/pipeline.log` (rotação de 5 MiB x 5 arquivos).
- **`.github/workflows/deploy_pages.yml`:** executa `npm run sources && npm run build:strict` e publica no GitHub Pages após sucesso do pipeline de dados ou alterações em `reports/` e `data/gold/**`.
- **`.github/workflows/codeql.yml`:** análise estática de segurança para Python e GitHub Actions.

## Documentação e governança

- [Documentação em português (Diátaxis)](docs/pt/README.md) · [Documentation in English](docs/en/README.md) · [Índice bilíngue](docs/README.md)
- [Decisões arquiteturais (ADRs 001–004)](docs/decisions/README.md)
- [Histórico de mudanças (CHANGELOG)](CHANGELOG.md)
- [Convenções e restrições operacionais (AGENTS.md)](AGENTS.md)
- Licença: [GNU GPL v3.0](LICENSE)
