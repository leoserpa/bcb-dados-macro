# Guias práticos

Receitas diretas para operação diária, consultas analíticas, compilação do dashboard e diagnóstico de falhas.

## Executar uma carga incremental

```bash
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

O pipeline reprocessa os últimos sete dias por série SGS e por moeda PTAX para capturar revisões tardias do BCB.

## Executar uma carga histórica ou backfill pontual

```bash
uv run python -m src.pipelines.run \
  --start-date 2010-01-01 \
  --end-date 2026-11-25 \
  --currency USD,EUR \
  --log-dir logs
```

Para incluir moedas adicionais em uma execução local, adicione códigos separados por vírgula em `--currency` (por exemplo, `USD,EUR,GBP`).

## Consultar juro real e regime monetário

```sql
SELECT
    data,
    selic_meta,
    ipca_focus_ano,
    juro_real_ex_ante,
    regime_monetario
FROM vw_macro_regime
ORDER BY data DESC
LIMIT 15;
```

Para acompanhar a série mensal comparando juro real ex-ante e ex-post:

```sql
SELECT *
FROM vw_juro_real_completo
ORDER BY data DESC
LIMIT 24;
```

## Comparar Focus Top 5 com o consenso geral

```sql
SELECT
    indicador,
    data_referencia,
    tipo_calculo,
    mediana_top5,
    mediana_geral,
    spread_top5_vs_geral
FROM vw_focus_top5_vs_geral
WHERE indicador = 'IPCA'
ORDER BY data_referencia, tipo_calculo;
```

Na tabela `focus_expectations`, `mediana` é uma expectativa de mercado para `data_referencia`, não um dado realizado.

## Ler arquivos Parquet diretamente com DuckDB

```sql
SELECT * FROM 'data/silver/sgs/sgs.parquet' LIMIT 10;
SELECT * FROM 'data/gold/ptax_daily.parquet' ORDER BY data_referencia DESC LIMIT 10;
```

## Compilar e validar o dashboard Evidence localmente

Sempre que atualizar `data/gold/bcb_macro.duckdb` ou editar páginas em `reports/pages/`:

```bash
cd reports
npm ci
npm run sources
npm run build:strict
```

Use `npm run build:strict` antes de abrir um Pull Request para garantir que nenhuma consulta SQL ou componente Svelte quebrou.

## Investigar uma falha

1. Leia os eventos JSON em `logs/pipeline.log`.
2. Verifique `failed_sources` no resumo JSON impresso no stdout (ex.: `"sgs:24364"`, `"focus_top5"`, `"ptax:EUR"`).
3. Rode novamente o quality gate:

```bash
uv run python -m src.pipelines.quality \
  --database data/gold/bcb_macro.duckdb \
  --max-staleness-days 10
```

4. Em indisponibilidade parcial, os dados Silver anteriores das fontes afetadas são preservados e o processo retorna código `2`. Reexecute o pipeline quando o endpoint do BCB normalizar.

## Executar pelo GitHub Actions

- **Pipeline de dados:** abra **Actions → BCB Data Pipeline → Run workflow** e informe opcionalmente `start_date`, `end_date` e `lookback_days`. A execução agendada ocorre de segunda a sexta às `12:30 UTC` (`09:30 BRT`).
- **Deploy do dashboard:** abra **Actions → Deploy Evidence Dashboard → Run workflow** ou aguarde o disparo automático após um push em `reports/` ou `data/gold/**` ou conclusão com sucesso do `BCB Data Pipeline`.

English version: [How-to guides](../en/how-to.md).
