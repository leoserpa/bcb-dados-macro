# AGENTS.md: Guia de Engenharia e Restrições do Repositório

Instruções operacionais e restrições verificadas para agentes e contribuidores no **BCB Macro Lakehouse**.

## Mapa do repositório

- `src/extractors/`: coletores das APIs públicas do BCB (`sgs.py` com 17 séries em `SGS_SERIES`; `olinda.py` para Focus, Focus Top 5 e PTAX com paginação OData).
- `src/models/schemas.py`: contratos Pydantic v2 (`extra="forbid"`) para registros Bronze → Silver (`SGSRecord`, `FocusRecord`, `FocusTop5Record`, `PTAXRecord`).
- `src/transformers/medallion.py`: schemas Polars explícitos e `upsert_parquet` idempotente consciente de conteúdo.
- `src/pipelines/run.py`: orquestrador CLI (`src.pipelines.run`; alias `src.pipeline.run`), lookback de 7 dias, isolamento de falha parcial (`exit 2`).
- `src/pipelines/gold.py`: rebuild atômico (`*.tmp.*` + `CHECKPOINT` + `.replace()`) de 7 tabelas e 6 views no DuckDB e 2 Parquets ZSTD.
- `src/pipelines/quality.py`: portão determinístico de qualidade sobre a camada Gold.
- `src/utils/`: cliente HTTP (`http_client.py`), logs JSON rotativos (`logging_config.py`) e armazenamento Bronze SHA-256 (`storage.py`).
- `tests/`: testes unitários e de integração com cobertura mínima de `85%`.
- `reports/`: dashboard Evidence.dev (`pages/*.md`, `components/*.svelte`, `sources/bcb_macro/*.sql`, `evidence.config.yaml`).
- `docs/`: documentação bilíngue Diátaxis (`pt/`, `en/`) e registros de decisão (`decisions/`).

## Comandos de verificação

### Python e qualidade de código

O arquivo `.python-version` define `3.14` (usado no CI). Em hosts Linux locais com Python `3.12`, passe `--frozen --python 3.12`:

```bash
uv run --frozen --python 3.12 ruff check .
uv run --frozen --python 3.12 ruff format --check .
uv run --frozen --python 3.12 pytest --cov=src --cov-fail-under=85 -q
```

Para executar o pipeline e validar a base Gold gerada:

```bash
uv run --frozen --python 3.12 python -m src.pipelines.run --lookback-days 7 --log-dir logs
uv run --frozen --python 3.12 python -m src.pipelines.quality --database data/gold/bcb_macro.duckdb --max-staleness-days 10
```

### Dashboard Evidence.dev

Requer Node.js 18+ (o CI utiliza Node 20):

```bash
cd reports
npm ci
npm run sources
npm run build:strict
```

## Restrições e armadilhas conhecidas

1. **Cast explícito `DATE` em views Gold (`src/pipelines/gold.py`):** qualquer agregação mensal com `date_trunc('month', data)` consumida pelo Evidence precisa de `CAST(... AS DATE)` explícito (como em `vw_juro_real_completo`), caso contrário `TIMESTAMP` quebra o binder de datas no DuckDB-WASM.
2. **Sintaxe de inputs no Evidence v40 (`reports/pages/`):** `<ButtonGroup name=x>` expõe o valor diretamente em `${inputs.x}`; `<Dropdown name=y>` expõe um objeto e exige `${inputs.y.value}`.
3. **Props Svelte em páginas Markdown:** não coloque crases literais dentro de strings de propriedades em componentes Svelte nas páginas `.md` do Evidence.
4. **Filtros de horizonte sem anos hardcoded:** em queries Focus (como `vw_focus_repricing`), derive anos futuros em relação a `YEAR(CURRENT_DATE)` quando o objetivo for manter as páginas válidas entre viradas de ano.
5. **Padrão de moeda PTAX (`src/pipelines/run.py`):** a CLI define `--currency` com padrão `"USD,EUR"`, enquanto a dataclass `PipelineConfig.currency` em chamadas Python diretas mantém `"USD"` como default se o argumento não for informado.
6. **Escopo do quality gate (`src/pipelines/quality.py`):** `EXPECTED_TABLES` valida os 6 objetos nucleares (`sgs_series`, `focus_expectations`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `vw_macro_latest`). As tabelas e views analíticas adicionais (`focus_top5`, `ptax_risk_metrics`, `vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral`, `vw_lakehouse_lineage`) são validadas pelo rebuild da Gold e pelo `npm run build:strict` do Evidence.
7. **Gramática visual do dashboard (`reports/`):** preserve o fundo escuro neutro (`#0f0f0f` / `#161616`), destaque focal único em `#ff6b00`, `Inter` (`tabular-nums`) para valores KPI, `IBM Plex Mono` para tabelas/datas e formatação condicional estritamente tipográfica (sem pílulas coloridas, bolinhas de status ou fundo colorido em linhas inteiras).
8. **Sincronia de documentação:** alterações em `SGS_SERIES`, endpoints Olinda, tabelas/views Gold, verificações de `quality.py` ou rotas de `reports/` exigem atualização conjunta em [docs/pt/reference.md](docs/pt/reference.md), [docs/en/reference.md](docs/en/reference.md), [README.md](README.md), [README.en.md](README.en.md) e [CHANGELOG.md](CHANGELOG.md). Decisões estruturais exigem novo ADR em [docs/decisions/](docs/decisions/README.md).
9. **Arquivos locais de skills:** `.agents/` e `skills-lock.json` estão no `.gitignore` e nunca devem ser commitados no repositório.
