# ADR-003: Dashboard estático com Evidence.dev e DuckDB-WASM no GitHub Pages

- **Status:** Aceito
- **Data:** 2026-11-25

## Contexto

Os dados tratados na camada Gold (`data/gold/bcb_macro.duckdb`) precisam ser exploráveis por analistas e usuários finais em um painel web interativo, acessível por URL pública e mantido no mesmo fluxo de CI/CD do pipeline Python.

Havia três necessidades principais:

1. **Custo zero de servidor e autenticação simples:** o repositório é open-source (GPL-3.0) hospedado no GitHub.
2. **Consultas SQL próximas do schema real:** gráficos e tabelas devem consultar diretamente as tabelas e views da camada Gold, sem manter uma API backend intermediária em sincronia.
3. **Detecção antecipada de regressões SQL:** alterações no schema do DuckDB ou em queries Markdown não podem quebrar páginas em produção silenciosamente.

## Decisão

Adotar o **Evidence.dev** (`reports/`, versão `^40.1.8` com `@evidence-dev/duckdb` `^2.0.1` e `@evidence-dev/core-components` `^5.4.2`) compilado como **aplicação estática** e publicado no GitHub Pages (`https://leoserpa.github.io/bcb-dados-macro/`) pelo workflow `.github/workflows/deploy_pages.yml`:

1. **Sincronização no build (`reports/package.json`):** o script `sync-db` copia `../data/gold/bcb_macro.duckdb` para `reports/sources/bcb_macro/bcb_macro.duckdb` (gitignored), e `npm run sources` materializa as 11 consultas SQL em dados para execução client-side via DuckDB-WASM.
2. **Build estrito obrigatório no CI (`npm run build:strict`):** o deploy só avança se todas as queries SQL nas fontes e nas 7 páginas Markdown compilarem sem erro de binding ou coluna inexistente.
3. **Tipagem explícita para DuckDB-WASM (`src/pipelines/gold.py`):** views que usam `date_trunc('month', data)` (como `vw_juro_real_completo`) executam `CAST(... AS DATE)` explicitamente na criação da view Gold, evitando incompatibilidade entre `TIMESTAMP` e `DATE` no binder do DuckDB-WASM no navegador.
4. **Fixação de peer dependency (`reports/package.json`):** `typescript` foi fixado em `^5.8.3` via `devDependencies` e `overrides` para que `npm ci` funcione sem `--legacy-peer-deps`.

## Alternativas consideradas

### 1. Streamlit ou Dash hospedado em PaaS externo
- **Prós:** código inteiramente em Python (extração e interface) e callbacks dinâmicos sem etapa de compilação estática.
- **Contras:** requer servidor ativo (cold starts em planos gratuitos, limites de uptime/sleeping), aumenta a superfície operacional fora do GitHub e separa a execução do dashboard do repositório estático.

### 2. Ferramenta BI tradicional (Metabase ou Apache Superset em container)
- **Prós:** interface visual consolidada e permissões multiusuário.
- **Contras:** exige hospedagem de container e banco de metadados próprio; dashboards não ficam versionados em Markdown/SQL legível por diff de Git junto com o código do pipeline.

### 3. Frontend React/Svelte customizado consumindo API FastAPI ou JSON estático pré-computado
- **Prós:** controle total de bundle e design sem restrições de framework.
- **Contras:** obriga escrever manualmente camadas de filtro client-side e endpoints de consulta em Python sempre que um novo indicador ou janela temporal é adicionado nas páginas.

## Consequências

### Positivas
- **Zero infraestrutura dedicada:** hospedagem estática gratuita no GitHub Pages disparada automaticamente após sucesso de `BCB Data Pipeline` ou em pushes para `reports/` e `data/gold/`.
- **Consultas versionadas em SQL:** todas as 11 fontes (`reports/sources/bcb_macro/*.sql`) e 7 páginas (`reports/pages/*.md`) passam por revisão de código normal no Git.
- **Proteção de deploy:** `npm run build:strict` interrompe o workflow se alguma view Gold ou página perder uma coluna esperada.

### Negativas
- **Dados refletem o último build:** alterações manuais no DuckDB local só aparecem online após commit em `data/gold/**` e término do workflow `Deploy Evidence Dashboard`.
- **Particularidades do Evidence v40:** componentes de entrada diferenciam a forma de leitura (`${inputs.grupo}` em `<ButtonGroup>` versus `${inputs.campo.value}` em `<Dropdown>`), e prop strings em Markdown não aceitam backticks literais.

### Neutras
- A URL base do build é configurada em `/bcb-dados-macro` (`reports/evidence.config.yaml`), espelhando o caminho padrão de publicação do GitHub Pages do projeto.
