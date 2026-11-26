# Referência técnica

Especificação exata de comandos, opções de linha de comando, fontes do BCB, chaves primárias, objetos da camada Gold, verificações de qualidade, dashboard e workflows.

## Comandos

### Pipeline Python (`uv`)

| Tarefa | Comando |
|---|---|
| Instalar dependências | `uv sync --frozen --dev` |
| Analisar estilo (Ruff) | `uv run ruff check .` |
| Verificar formatação | `uv run ruff format --check .` |
| Executar testes e cobertura | `uv run pytest --cov=src --cov-fail-under=85 -q` |
| Executar ingestão | `uv run python -m src.pipelines.run` |
| Validar qualidade da Gold | `uv run python -m src.pipelines.quality` |

> Em máquinas sem Python 3.14 instalado, adicione `--frozen --python 3.12` após `uv run`. O alias `python -m src.pipeline.run` redireciona para `src.pipelines.run`.

### Dashboard Evidence (`reports/`)

| Script (`npm run <script>`) | Ação |
|---|---|
| `sync-db` | Copia `../data/gold/bcb_macro.duckdb` para `reports/sources/bcb_macro/bcb_macro.duckdb` |
| `sources` | Executa `sync-db` e materializa as 11 fontes SQL (`evidence sources`) |
| `sources:strict` | Executa `sync-db` e `evidence sources --strict` |
| `dev` | Executa `sync-db` e abre servidor local em `/bcb-dados-macro` |
| `build` | Compila o site estático em `reports/build/` |
| `build:strict` | Compila falhando em qualquer erro SQL ou de componente |
| `preview` | Visualiza o build estático gerado |

## Opções de linha de comando

### `src.pipelines.run`

| Opção | Tipo | Padrão | Descrição |
|---|---|---|---|
| `--start-date` | `YYYY-MM-DD` | `None` (usa lookback/inicial) | Sobrescreve a data inicial de coleta |
| `--end-date` | `YYYY-MM-DD` | Hoje em `America/Sao_Paulo` | Data final da coleta |
| `--lookback-days` | `int` | `7` | Dias reprocessados a partir da última data persistida |
| `--currency` | `str` | `"USD,EUR"` | Moedas PTAX separadas por vírgula |
| `--data-root` | `Path` | `data/` | Diretório raiz das camadas Bronze/Silver/Gold |
| `--log-dir` | `Path` | `logs/` | Diretório de saída para `pipeline.log` |

- **Nota:** chamadas diretas em Python usando `PipelineConfig` sem informar `currency` assumem `"USD"` como default do dataclass; a CLI define `"USD,EUR"`.
- **Códigos de saída:** `0` quando todas as fontes concluem; `2` em falha parcial (fontes saudáveis são atualizadas e fontes com erro preservam o último estado Silver).

### `src.pipelines.quality`

| Opção | Tipo | Padrão | Descrição |
|---|---|---|---|
| `--database` | `Path` | `data/gold/bcb_macro.duckdb` | Caminho do arquivo DuckDB a validar |
| `--as-of-date` | `YYYY-MM-DD` | Hoje em `America/Sao_Paulo` | Data de referência para datas futuras e defasagem |
| `--max-staleness-days` | `int` | `None` | Limite máximo de atraso em dias para SGS, Focus e PTAX |

- **Código de saída:** `0` quando `passed = true`; `1` quando alguma checagem crítica falha.

## Fontes configuradas

### SGS (`src/extractors/sgs.py`) — 17 séries

Consultadas via `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados` em blocos de até `3650` dias (`max_span_days`). HTTP `404` e payloads JSON `{"erro": {"statusCode": 404}}` em janelas vazias são registrados e ignorados.

| Código | Nome da série | Frequência |
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

Paginação OData com `page_size = 1000` via `@odata.nextLink`, fallback para `$skip` e proteção contra loops (`visited_urls`).

| Fonte | Endpoint Olinda | Escopo configurado |
|---|---|---|
| Focus | `Expectativas/versao/v1/odata/ExpectativasMercadoAnuais` | Indicadores `IPCA`, `Selic`, `Câmbio`, `PIB Total` |
| Focus Top 5 | `Expectativas/versao/v1/odata/ExpectativasMercadoTop5Anuais` | Indicadores `IPCA`, `Selic`, `Câmbio`, `PIB Total` (`tipoCalculo`: `C`, `M`, `L`) |
| PTAX | `PTAX/versao/v1/odata/CotacaoMoedaPeriodo(...)` | Boletins intradia para moedas em `--currency` (`USD,EUR` na CLI) |

## Camadas Bronze e Silver

- **Bronze (`src/utils/storage.py`):** arquivos JSON imutáveis em `data/bronze/source=<fonte>/ingestion_date=YYYY-MM-DD/<arquivo>__<sha256[:16]>.json` com hash SHA-256 canônico e metadados da requisição.
- **Silver (`src/models/schemas.py`, `src/transformers/medallion.py`):** contratos Pydantic v2 (`extra="forbid"`) gravados em Parquet com compressão ZSTD e estatísticas habilitadas. O upsert preserva o menor `ingested_at` quando todas as colunas de negócio são idênticas e mantém o último registro por chave quando há revisão.

| Conjunto Silver | Arquivo | Chave primária | Normalização / filtro |
|---|---|---|---|
| SGS | `data/silver/sgs/sgs.parquet` | `data`, `codigo_serie` | `retain_rows` mantém apenas códigos em `SGS_SERIES` |
| Focus | `data/silver/focus/focus.parquet` | `data`, `indicador`, `data_referencia`, `indicador_detalhe`, `base_calculo` | `indicador_detalhe` nulo → `""`; `base_calculo` nulo → `-1` |
| Focus Top 5 | `data/silver/focus_top5/focus_top5.parquet` | `data`, `indicador`, `data_referencia`, `tipo_calculo` | `tipo_calculo` normalizado com `.strip()` |
| PTAX | `data/silver/ptax/ptax.parquet` | `data_hora_cotacao`, `moeda`, `tipo_boletim` | `data_referencia` derivada de `data_hora_cotacao` se ausente |

## Camada Gold (`src/pipelines/gold.py`)

Reconstruída atomicamente via arquivos temporários (`bcb_macro.tmp.duckdb`, `*.tmp.parquet`), `CHECKPOINT`, fechamento da conexão e substituição atômica (`replace()`).

### Tabelas (7)

| Tabela | Descrição |
|---|---|
| `sgs_series` | Cópia tipada das 17 séries em `sgs.parquet` |
| `focus_expectations` | Expectativas anuais de `focus.parquet` |
| `focus_top5` | Projeções anuais Top 5 de `focus_top5.parquet` |
| `ptax_quotes` | Todos os boletins PTAX intradia de `ptax.parquet` |
| `macro_indicators` | União em formato longo de `sgs_series` (`fonte='SGS'`) e `focus_expectations` (`fonte='FOCUS'`) |
| `ptax_daily` | Uma cotação prioritária por `(data_referencia, moeda)`, priorizando `tipo_boletim = 'Fechamento'` e depois maior `data_hora_cotacao` |
| `ptax_risk_metrics` | Spread (`cotacao_venda - cotacao_compra`), `retorno_diario_pct`, médias móveis `media_movel_21d` e `media_movel_252d`, `vol_anualizada_21d` (`STDDEV_SAMP(log_return) * SQRT(252) * 100`) e `zscore_252d` |

### Views (6)

| View | Regra principal |
|---|---|
| `vw_macro_latest` | Última `data_observacao` por `fonte`, `indicador_id`, horizonte (vazio para SGS), `metrica` e `detalhe` |
| `vw_focus_repricing` | Compara última mediana `base_calculo = 0` (30d) contra `base_calculo = 1` (5d úteis), calculando `repricing_b1_vs_b0` e `drift_30d` via `LAG(mediana, 21)` |
| `vw_macro_regime` | Junta SGS `432` com mediana Focus `IPCA` (`base_calculo = 0`, ano corrente); calcula juro real ex-ante de Fisher `((1 + selic_meta/100) / (1 + ipca_focus_ano/100) - 1) * 100` e classifica `>= 6.0` como `Restritivo`, `>= 3.5` como `Neutro` e `< 3.5` como `Expansionista` |
| `vw_juro_real_completo` | Série mensal combinando Meta Selic (`432`), IPCA 12m (`13522`) e `vw_macro_regime` para expor `juro_real_ex_post` e `juro_real_ex_ante`, com `CAST(date_trunc('month', data) AS DATE)` explícito |
| `vw_focus_top5_vs_geral` | Última mediana de `focus_top5` por `(indicador, data_referencia, tipo_calculo)` comparada à última mediana geral (`base_calculo = 0`), calculando `spread_top5_vs_geral` |
| `vw_lakehouse_lineage` | Contagem, `data_minima`, `data_maxima` e `ultima_ingestao` em `sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`, `ptax_daily` e `macro_indicators` |

### Exportações Parquet da Gold

- `data/gold/macro_indicators.parquet` (ZSTD)
- `data/gold/ptax_daily.parquet` (ZSTD)

## Verificações de qualidade (`src/pipelines/quality.py`)

O quality gate executa verificações críticas em `bcb_macro.duckdb`:

- **Presença de objetos (`EXPECTED_TABLES`):** `sgs_series`, `focus_expectations`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `vw_macro_latest`.
- **Esquema e não nulidade:** colunas obrigatórias e contagem zero de nulos em `sgs_series`, `focus_expectations` e `ptax_quotes`.
- **Tabelas não vazias e chaves únicas:** valida ausência de duplicatas para as PKs de SGS, Focus e PTAX.
- **Domínios e finitude:** confere todas as 17 séries em `EXPECTED_SGS_SERIES`, os 4 indicadores em `EXPECTED_FOCUS_INDICATORS` e `isfinite()` nos valores numéricos.
- **Reconciliação:** `COUNT(macro_indicators) == COUNT(sgs_series) + COUNT(focus_expectations)` e `0 < COUNT(ptax_daily) <= COUNT(ptax_quotes)`.
- **Datas e atualização:** ausência de datas posteriores a `--as-of-date` e verificação opcional contra `--max-staleness-days`.

> **Escopo conhecido:** `focus_top5`, `ptax_risk_metrics` e as 5 views analíticas derivadas (`vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral`, `vw_lakehouse_lineage`) não integram `EXPECTED_TABLES` em `quality.py`; sua integridade estrutural é validada na reconstrução da Gold e na compilação estrita do Evidence (`npm run sources && npm run build:strict`).

## Dashboard Evidence (`reports/`)

- **Base URL:** `/bcb-dados-macro` (`reports/evidence.config.yaml`)
- **Dependências principais:** `@evidence-dev/evidence` `^40.1.8`, `@evidence-dev/core-components` `^5.4.2`, `@evidence-dev/duckdb` `^2.0.1`, `typescript` `^5.8.3`
- **Páginas (`reports/pages/`):**
  - `/` (`index.md`) — Panorama
  - `/inteligencia-de-mercado` (`inteligencia-de-mercado.md`) — Inteligência de Mercado & Simulador
  - `/juros-e-atividade` (`juros-e-atividade.md`) — Juros & Atividade
  - `/inflacao-e-trabalho` (`inflacao-e-trabalho.md`) — Inflação & Trabalho
  - `/cambio` (`cambio.md`) — Câmbio & Setor Externo
  - `/focus` (`focus.md`) — Expectativas Focus
  - `/qualidade-e-linhagem` (`qualidade-e-linhagem.md`) — Qualidade & Linhagem
- **Fontes SQL (`reports/sources/bcb_macro/`):** 11 consultas espelhando `sgs_series`, `focus_expectations`, `focus_top5`, `ptax_daily`, `ptax_risk_metrics`, `vw_macro_latest`, `vw_focus_repricing`, `vw_macro_regime`, `vw_juro_real_completo`, `vw_focus_top5_vs_geral` e `vw_lakehouse_lineage`.
- **Componentes customizados (`reports/components/`):** `KPITerminalCard.svelte`, `ExecutiveTable.svelte`, `ConditionalTable.svelte`, `TerminalLineChart.svelte`, `FilterBar.svelte`.

## Rede, logs e CI/CD

- **Cliente HTTP (`src/utils/http_client.py`):** timeout padrão de `30s`; `ExponentialRetry` com `total=3` (`connect=3`, `read=3`, `status=3`) em métodos `GET` para status `429, 500, 502, 503, 504`, backoff de `2s`, `4s` e `8s`, pool de `10` conexões.
- **Logging (`src/utils/logging_config.py`):** uma linha JSON por evento no terminal e em `logs/pipeline.log` via `RotatingFileHandler` (`5 MiB` por arquivo, `5` backups).
- **Variável de ambiente e Python:** `BCB_INITIAL_DATE` sobrescreve o início padrão (`2010-01-01`). `pyproject.toml` define `requires-python = ">=3.11"`; `.python-version` e o CI utilizam Python `3.14`.
- **Workflows (`.github/workflows/`):**
  - `data_pipeline.yml`: segunda a sexta às `12:30 UTC` (`09:30 BRT`) ou manual; roda Ruff, Pytest (`--cov-fail-under=85`), ingestão, quality gate (`--max-staleness-days 10`) e commit automático em `data/`.
  - `deploy_pages.yml`: dispara em pushes em `data/gold/**` ou `reports/**`, após conclusão bem-sucedida de `BCB Data Pipeline` ou manualmente; executa `npm run sources && npm run build:strict` no Node 20 e publica no GitHub Pages.
  - `codeql.yml`: análise estática em `python` e `actions` em pushes/PRs para `main` e às segundas `14:00 UTC`.

English version: [Technical reference](../en/reference.md).
