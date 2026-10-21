# Explicação da arquitetura

## Por que usar a arquitetura Medallion?

Bronze preserva o payload original e os metadados da requisição. Silver converte esses dados em contratos estáveis, datas ISO, números `Float64`, registros deduplicados e arquivos Parquet. Gold organiza tabelas analíticas no DuckDB e oferece visões SQL.

Essa separação permite reprocessar transformações sem consultar novamente a API e mantém evidências da origem coletada.

## Como a idempotência funciona?

Cada conjunto tem uma chave explícita. O upsert substitui revisões do BCB para a mesma chave e evita duplicações em execuções repetidas. A janela de reprocessamento captura correções recentes sem refazer toda a carga histórica.

## Por que Parquet e DuckDB?

Parquet é colunar e portátil, adequado para a camada Silver. DuckDB fornece SQL analítico local e persiste a camada Gold. Os formatos atendem a funções diferentes dentro do lakehouse.

## Como a confiabilidade é verificada?

As requisições HTTP usam timeout e retries exponenciais. Pydantic valida contratos de entrada, Polars aplica schemas, o quality gate verifica invariantes e Pytest cobre extratores, transformações, armazenamento e integração.

## O que é uma falha parcial?

Se uma fonte falhar, os dados anteriores dela são preservados e o resumo lista `failed_sources`. O processo termina com código `2` para indicar que a execução não foi completa.

English version: [Architecture explanation](../en/explanation.md).
