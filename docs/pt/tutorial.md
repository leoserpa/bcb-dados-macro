# Tutorial: primeira execução

Este tutorial leva você da preparação do ambiente até uma base Gold validada.

## 1. Preparar o ambiente

No PowerShell, na raiz do repositório:

```powershell
uv python install 3.14
uv sync --dev
```

## 2. Verificar o código

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

## 3. Baixar o histórico

```powershell
uv run python -m src.pipelines.run `
  --start-date 2010-01-01 `
  --end-date 2026-10-21 `
  --log-dir logs
```

Troque `2026-10-21` pela data final desejada. A carga cria os snapshots Bronze, atualiza os Parquet Silver e reconstrói Gold quando os dados mudam.

## 4. Validar os dados

```powershell
uv run python -m src.pipelines.quality `
  --database data\gold\bcb_macro.duckdb `
  --as-of-date 2026-10-21 `
  --max-staleness-days 10
```

O campo `passed` deve ser `true`.

## 5. Consultar as tabelas

```powershell
uv run python -c "import duckdb; c=duckdb.connect('data/gold/bcb_macro.duckdb'); print(c.sql('SHOW TABLES'))"
```

English version: [First run tutorial](../en/tutorial.md).
