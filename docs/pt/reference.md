# Referência técnica

## Comandos

| Tarefa | Comando |
|---|---|
| Instalar dependências | `uv sync --dev` |
| Analisar estilo | `uv run ruff check .` |
| Verificar formatação | `uv run ruff format --check .` |
| Executar testes | `uv run pytest -q` |
| Executar ingestão | `uv run python -m src.pipelines.run` |
| Validar qualidade | `uv run python -m src.pipelines.quality` |

## Opções de linha de comando

`src.pipelines.run` aceita `--start-date`, `--end-date`, `--lookback-days`, `--currency`, `--data-root` e `--log-dir`. As datas usam `YYYY-MM-DD`; a moeda padrão é `USD`.

`src.pipelines.quality` aceita `--database`, `--as-of-date` e `--max-staleness-days`.

## Fontes configuradas

- **SGS:** séries `11`, `432`, `13762`, `13967`, `13970`, `13982`, `20631`, `21082` e `24364`.
- **Focus:** indicadores `IPCA`, `Selic`, `Câmbio` e `PIB Total`.
- **PTAX:** cotações de USD.

## Chaves idempotentes

| Conjunto | Chave |
|---|---|
| SGS | `data`, `codigo_serie` |
| Focus | `data`, `indicador`, `data_referencia`, `indicador_detalhe`, `base_calculo` |
| PTAX | `data_hora_cotacao`, `moeda`, `tipo_boletim` |

## Tabelas Gold

- `sgs_series`: observações SGS tipadas.
- `focus_expectations`: expectativas anuais de mercado.
- `ptax_quotes`: boletins de cotações PTAX.
- `ptax_daily`: cotação prioritária diária por moeda.
- `macro_indicators`: valores observados e medianas Focus em formato longo.
- `vw_macro_latest`: observação mais recente por indicador, período de referência e métrica.

## Verificações de qualidade

O quality gate verifica tabelas e colunas obrigatórias, conjuntos não vazios, nulos, unicidade das chaves, domínios esperados, valores numéricos finitos, reconciliação da Gold, datas futuras e atualização das fontes.

## Configuração

`BCB_INITIAL_DATE` altera a data inicial padrão. O projeto exige Python `>=3.11`; o ambiente de desenvolvimento usa Python 3.14.

English version: [Technical reference](../en/reference.md).
