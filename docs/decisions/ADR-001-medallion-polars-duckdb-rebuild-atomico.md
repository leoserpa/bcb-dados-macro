# ADR-001: Arquitetura Medallion com Polars, DuckDB e rebuild atômico da camada Gold

- **Status:** Aceito
- **Data:** 2026-11-25

## Contexto

O projeto coleta séries públicas das APIs SGS e Olinda do Banco Central do Brasil (BCB), consolida o histórico desde `2010-01-01` e serve os resultados em um repositório Git sem infraestrutura gerenciada de banco de dados.

Era necessário resolver quatro restrições simultaneamente:

1. **Auditabilidade e reprocessamento:** bugs de parsing ou novas regras de tipagem não podem exigir nova coleta de toda a série histórica nas APIs do BCB.
2. **Contratos rígidos:** respostas JSON heterogêneas do BCB (números com vírgula decimal, strings `"nan"` ou `"-"`, campos opcionais no Focus) precisam de validação estrita antes de entrar nas tabelas analíticas.
3. **Consultas analíticas locais rápidas:** o ambiente de CI e o dashboard precisam executar janelas móveis (`ptax_risk_metrics`), joins e agregações SQL em poucos segundos.
4. **Consistência em disco:** falhas durante a geração do banco analítico não podem deixar `data/gold/bcb_macro.duckdb` ou os Parquets Gold corrompidos ou parcialmente atualizados.

## Decisão

Adotar uma arquitetura **Medallion em três camadas** no armazenamento local (`data/`), combinada com **rebuild completo e atômico** da camada Gold sempre que houver alteração na Silver ou ausência do arquivo DuckDB:

1. **Bronze (`src/utils/storage.py`):** grava snapshots JSON imutáveis particionados por `source=<fonte>/ingestion_date=YYYY-MM-DD/<nome>__<sha256[:16]>.json`, incluindo metadados da requisição e hash SHA-256 do payload canônico. A escrita usa arquivo temporário `.tmp` seguido de `replace()`.
2. **Silver (`src/models/schemas.py`, `src/transformers/medallion.py`):** valida registros em contratos Pydantic v2 (`extra="forbid"`), converte para schemas explícitos em **Polars** e persiste datasets tipados em **Parquet com compressão ZSTD** e estatísticas habilitadas (`sgs.parquet`, `focus.parquet`, `focus_top5.parquet`, `ptax.parquet`).
3. **Gold (`src/pipelines/gold.py`):** lê apenas os arquivos Parquet da Silver e constrói do zero as 7 tabelas e 6 views analíticas dentro de `bcb_macro.tmp.duckdb`, exportando também `macro_indicators.tmp.parquet` e `ptax_daily.tmp.parquet`. Após `CHECKPOINT` e fechamento da conexão, substitui atomicamente os arquivos finais e remove resíduos `.wal`. Quando a Silver não sofre alterações e o `.duckdb` já existe, o rebuild da Gold é pulado.

## Alternativas consideradas

### 1. Gravar diretamente em SQLite ou DuckDB sem Bronze e Silver
- **Prós:** menos arquivos no repositório e ausência de etapa intermediária em Parquet.
- **Contras:** acopla o formato bruto da API ao schema analítico. Mudanças de transformação ou correções de parsing exigiriam reconsultar toda a API desde 2010, sem trilha do payload original nem deduplicação portável por dataset.

### 2. Banco relacional ou Data Warehouse gerenciado (PostgreSQL, BigQuery, Snowflake)
- **Prós:** suporte nativo a múltiplos escritores concorrentes, controle fino de acesso e armazenamento ilimitado de histórico.
- **Contras:** introduz custos recorrentes, credenciais em runtime, latência de rede no CI e impede o empacotamento autônomo dos dados no repositório para consumo direto pelo Evidence.dev no GitHub Pages.

### 3. Pandas + CSV intermediário
- **Prós:** familiaridade ampla e zero dependência de formatos binários na Silver.
- **Contras:** CSV não preserva tipos nativos (`Date`, `Datetime` com fuso UTC, `Float64`, `Int64`), consome muito mais espaço no Git e torna scans e deduplicação em memória consideravelmente mais lentos que Polars sobre Parquet colunar.

### 4. Atualização incremental (`INSERT`/`UPDATE`/`DELETE`) no DuckDB Gold em produção
- **Prós:** evita reescrever linhas antigas em `sgs_series`, `focus_expectations` e `ptax_quotes`.
- **Contras:** aumenta o risco de inconsistência entre tabelas base e tabelas/views derivadas por janela completa (`ptax_risk_metrics`, `vw_macro_regime`, `vw_juro_real_completo`), gera crescimento de WAL entre execuções e dificulta garantir builds determinísticos quando views SQL são alteradas.

## Consequências

### Positivas
- **Zero corrupção parcial na Gold:** se ocorrer qualquer erro SQL ou de I/O durante `build_gold`, apenas arquivos `.tmp` são removidos; o banco anterior permanece intacto.
- **Silver como fonte de verdade portável:** qualquer cliente DuckDB, Polars ou PyArrow lê os Parquets em `data/silver/` diretamente sem depender de servidores.
- **Reprodutibilidade:** um rebuild de Gold depende exclusivamente dos Parquets Silver e do SQL versionado em `src/pipelines/gold.py`.

### Negativas
- **Custo proporcional ao tamanho total:** o tempo do rebuild Gold cresce com o histórico acumulado na Silver, embora permaneça baixo para séries macroeconômicas mensais e diárias desde 2010.
- **Versionamento binário no Git:** Parquet e DuckDB geram diffs binários no histórico do Git sempre que novos pregões ou divulgações do BCB alteram os arquivos.

### Neutras
- `data/gold/macro_indicators.parquet` e `data/gold/ptax_daily.parquet` replicam duas tabelas do DuckDB em ZSTD Parquet para consumidores externos que preferem leitura direta sem abrir `.duckdb`.
