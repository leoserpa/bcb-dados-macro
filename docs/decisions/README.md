# Architecture Decision Records (ADRs)

Este diretório registra as decisões arquiteturais relevantes do **BCB Macro Lakehouse**. Os registros explicam o contexto do problema, as alternativas descartadas e os trade-offs aceitos no código e no dashboard.

Os ADRs são mantidos em português brasileiro como registro principal e referenciados pela documentação em [português](../pt/README.md) e em [inglês](../en/README.md).

## Índice de decisões

| ID | Decisão | Status | Data | Resumo |
|---|---|---|---|---|
| [ADR-001](ADR-001-medallion-polars-duckdb-rebuild-atomico.md) | Arquitetura Medallion com Polars, DuckDB e rebuild atômico da Gold | Aceito | 2026-11-25 | Separação Bronze/Silver/Gold local em JSON SHA-256, Parquet ZSTD e rebuild atômico em DuckDB |
| [ADR-002](ADR-002-ingestao-incremental-lookback-e-falha-parcial.md) | Ingestão incremental com lookback de 7 dias e isolamento de falha parcial | Aceito | 2026-11-25 | Janela de revisão tardia, upsert consciente de conteúdo e código de saída `2` em falhas parciais |
| [ADR-003](ADR-003-evidence-static-bi-e-duckdb-wasm.md) | Dashboard estático com Evidence.dev e DuckDB-WASM no GitHub Pages | Aceito | 2026-11-25 | Compilação estática SQL-em-Markdown com `build:strict` e tipagem explícita `DATE` nas views Gold |
| [ADR-004](ADR-004-gramatica-visual-editorial-e-formatacao-tipografica.md) | Gramática visual editorial (Bloomberg Orange) e formatação tipográfica | Aceito | 2026-11-25 | Superfícies escuras neutras, foco único em `#ff6b00`, rótulos diretos e unidades sensíveis à linha |

## Como propor ou substituir uma decisão

1. Crie um novo arquivo sequencial (`ADR-NNN-titulo-curto.md`) usando a estrutura: Status, Data, Contexto, Decisão, Alternativas consideradas e Consequências.
2. Nunca apague ou reescreva silenciosamente um ADR aceito. Se uma decisão mudar, atualize o status do registro antigo para `Substituído por ADR-NNN` e documente os motivos no novo arquivo.
3. Atualize a tabela acima no mesmo commit.
