# Architecture explanation

## Why use the Medallion Architecture?

Bronze preserves the original payload and request metadata. Silver converts those records into stable contracts, ISO dates, `Float64` numbers, deduplicated records, and Parquet files. Gold organizes analytical tables in DuckDB and provides SQL views.

This separation allows transformations to be reprocessed without fetching the API again and preserves evidence of the collected source data.

## How does idempotency work?

Each dataset has an explicit key. Upserts replace BCB revisions with the same key and prevent duplicates across repeated runs. The lookback window captures recent corrections without repeating the full historical load.

## Why both Parquet and DuckDB?

Parquet is columnar and portable, making it suitable for Silver. DuckDB provides local analytical SQL and persists Gold. The formats serve different roles in the lakehouse.

## How is reliability checked?

HTTP requests use timeouts and exponential retries. Pydantic validates input contracts, Polars enforces schemas, the quality gate checks invariants, and Pytest covers extractors, transformations, storage, and integration.

## What is a partial failure?

If a source fails, its previous data is preserved and the summary lists it in `failed_sources`. The process exits with code `2` to make the incomplete run visible.

Versão em português: [Explicação da arquitetura](../pt/explanation.md).
