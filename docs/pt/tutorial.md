# Tutorial: primeira execução

Este tutorial orienta você da configuração do ambiente até uma base Gold validada e o dashboard local em execução.

## 1. Preparar o ambiente

Na raiz do repositório (em Linux/macOS; no Windows PowerShell, use `\` no lugar de `/` caso prefira):

```bash
uv python install 3.14
uv sync --frozen --dev
```

> Se sua máquina local usa apenas Python 3.12, execute os comandos `uv run` seguintes com `--frozen --python 3.12`.

## 2. Verificar código e testes

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=src --cov-fail-under=85 -q
```

## 3. Baixar o histórico

```bash
uv run python -m src.pipelines.run \
  --start-date 2010-01-01 \
  --end-date 2026-11-25 \
  --currency USD,EUR \
  --log-dir logs
```

Troque `2026-11-25` pela data desejada no formato `YYYY-MM-DD`. A carga grava os snapshots JSON na Bronze, atualiza os 4 conjuntos Parquet na Silver e constrói `data/gold/bcb_macro.duckdb` junto com `macro_indicators.parquet` e `ptax_daily.parquet`.

## 4. Validar a qualidade dos dados

```bash
uv run python -m src.pipelines.quality \
  --database data/gold/bcb_macro.duckdb \
  --as-of-date 2026-11-25 \
  --max-staleness-days 10
```

O campo `passed` no JSON retornado deve ser `true`.

## 5. Consultar os objetos Gold

```bash
uv run python -c "import duckdb; c=duckdb.connect('data/gold/bcb_macro.duckdb'); print(c.sql('SHOW ALL TABLES'))"
```

Você verá as 7 tabelas (`sgs_series`, `focus_expectations`, `focus_top5`, `ptax_quotes`, `macro_indicators`, `ptax_daily`, `ptax_risk_metrics`) e as 6 views analíticas.

## 6. Abrir o dashboard localmente (opcional)

Requer Node.js 18+ (Node 20 recomendado):

```bash
cd reports
npm install
npm run sources
npm run dev
```

O servidor local abre em `http://localhost:3000/bcb-dados-macro`.

English version: [First run tutorial](../en/tutorial.md).
