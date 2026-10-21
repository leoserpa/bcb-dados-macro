# Guias práticos

## Executar uma carga incremental

```powershell
uv run python -m src.pipelines.run --lookback-days 7 --log-dir logs
```

O pipeline reprocessa os últimos sete dias para capturar revisões tardias do BCB.

## Executar uma carga histórica

```powershell
uv run python -m src.pipelines.run `
  --start-date 2010-01-01 `
  --end-date 2026-10-21 `
  --currency USD `
  --log-dir logs
```

## Consultar expectativas Focus para Selic

```sql
SELECT data, data_referencia, mediana, media, base_calculo
FROM focus_expectations
WHERE indicador = 'Selic'
ORDER BY data DESC, data_referencia
LIMIT 20;
```

`mediana` é uma expectativa de mercado para o período indicado em `data_referencia`; não é a decisão atual do Copom. Valores históricos como 7,0 ou 6,5 podem ser previsões válidas para anos de referência diferentes.

## Ler um arquivo Parquet com SQL

```sql
SELECT * FROM 'data/silver/sgs/sgs.parquet' LIMIT 10;
```

## Investigar uma falha

1. Consulte `logs/pipeline.log`.
2. Veja `failed_sources` no resumo JSON.
3. Execute novamente o quality gate.
4. Se uma fonte estiver indisponível, os dados Silver anteriores são preservados. Uma carga parcial termina com código `2`.
5. Tente novamente quando a API do BCB estiver disponível.

## Executar pelo GitHub Actions

Abra **Actions → BCB Data Pipeline → Run workflow** e, se necessário, informe `start_date`, `end_date` e `lookback_days`. A execução agendada ocorre de segunda a sexta às 12:30 UTC (09:30 BRT).

English version: [How-to guides](../en/how-to.md).
