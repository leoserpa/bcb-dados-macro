# ADR-002: Ingestão incremental com lookback de 7 dias e isolamento de falha parcial

- **Status:** Aceito
- **Data:** 2026-11-25

## Contexto

As APIs do BCB apresentam três comportamentos operacionais que afetam cargas diárias automatizadas:

1. **Revisões retroativas:** indicadores como IBC-Br, concessões de crédito, séries fiscais (DLSP/PIB, DBGG/PIB, resultado primário) e boletins PTAX podem sofrer ajustes ou inclusões tardias alguns dias após a data inicial de referência.
2. **Restrições de janela na API SGS:** consultas de longos períodos em uma única requisição no SGS atingem limites da API do BCB; além disso, intervalos sem observações (por exemplo, séries mais recentes ou fins de semana) podem retornar HTTP `404` ou payload JSON `{"erro": {"statusCode": 404}}`.
3. **Instabilidade pontual de upstream:** timeouts ou códigos `429`/`5xx` em uma série específica do SGS ou em um endpoint do Olinda (Focus, Focus Top 5 ou uma moeda da PTAX) não devem apagar dados saudáveis nem interromper a atualização das demais fontes.

## Decisão

Implementar quatro mecanismos coordenados de extração e upsert (`src/extractors/`, `src/transformers/medallion.py`, `src/pipelines/run.py`, `src/utils/http_client.py`):

1. **Lookback incremental de 7 dias por série e por moeda:** sem `--start-date`, cada série SGS e cada moeda PTAX calcula o início como `max(initial_date, latest_date - timedelta(days=lookback_days))` com `lookback_days = 7` e `initial_date = 2010-01-01` (configurável por `BCB_INITIAL_DATE`). Focus e Focus Top 5 aplicam a mesma lógica sobre a coluna `data`.
2. **Upsert idempotente consciente de conteúdo em `upsert_parquet`:** antes de deduplicar pela chave primária mantendo o último `ingested_at`, o pipeline deduplica todas as colunas de negócio (`content_columns != "ingested_at"`) mantendo o **primeiro** `ingested_at`. Se a reconsulta de 7 dias retornar exatamente os mesmos valores, os timestamps originais são preservados, `existing.equals(final)` resulta em `changed = False`, o arquivo Parquet não é reescrito e a Gold não é reconstruída. Para a tabela SGS, `retain_rows` também filtra apenas séries presentes em `SGS_SERIES`.
3. **Janelas de até 10 anos e retries exponenciais fixos:** `SGSExtractor` divide intervalos longos em blocos de `max_span_days = 3650` e ignora janelas `404` sem abortar; `OlindaExtractor` pagina OData em blocos de `page_size = 1000` seguindo `@odata.nextLink` com fallback em `$skip` e detector de loop (`visited_urls`). O cliente HTTP (`create_http_session`) usa timeout de `30s` e 3 tentativas (`ExponentialRetry`) com espera exata de `2s`, `4s` e `8s` para status `429, 500, 502, 503, 504`.
4. **Isolamento de falha parcial com código de saída `2`:** erros de rede ou `ExtractionError` em uma fonte registram o identificador em `failed_sources` (ex.: `sgs:432`, `focus_top5`, `ptax:EUR`), preservam o conjunto anterior na Silver e permitem que as fontes saudáveis sejam persistidas. Ao final, se `failed_sources` não estiver vazio, `main()` encerra o processo com **código `2`**.

## Alternativas consideradas

### 1. Recarga histórica completa a cada execução diária
- **Prós:** garante captura de qualquer revisão histórica, independentemente da idade.
- **Contras:** multiplica o volume de chamadas nas APIs públicas do BCB a cada dia útil, aumenta o risco de rate limit (`429`) e falha por timeout em janelas longas.

### 2. Watermark estrito (`latest_date + 1 dia`, sem lookback)
- **Prós:** menor volume possível de registros reprocessados.
- **Contras:** perde revisões retroativas publicadas pelo BCB para datas já existentes na Silver e ignora correções intradia de fechamento PTAX caso uma coleta tenha ocorrido antes do boletim final.

### 3. Falha imediata (`fail-fast`) no primeiro erro de API
- **Prós:** comportamento simples de tratar em orquestradores.
- **Contras:** uma instabilidade isolada em uma única série SGS bloquearia a atualização diária da Selic, do IPCA, do Focus e da PTAX de todo o restante do lakehouse.

## Consequências

### Positivas
- **Zero commits vazios:** reexecuções consecutivas sem novos dados ou revisões não reescrevem Parquets Silver nem disparam rebuilds desnecessários de Gold ou GitHub Pages.
- **Degradação controlada:** os dados históricos anteriores na Silver permanecem íntegros mesmo quando uma API específica do BCB fica indisponível.

### Negativas
- **Revisões mais antigas que 7 dias exigem backfill manual:** correções publicadas meses depois só entram com `--start-date YYYY-MM-DD`.
- **Código de saída `2` sinaliza erro no GitHub Actions:** o step de ingestão falha no workflow `data_pipeline.yml` quando há falha parcial, exigindo atenção ou nova execução, e impede o commit automático até a recuperação da fonte.

### Neutras
- A CLI usa `--currency USD,EUR` por padrão (`src/pipelines/run.py`), enquanto `PipelineConfig.currency` em chamadas diretas Python mantém `"USD"` como default se o campo não for passado explicitamente.
