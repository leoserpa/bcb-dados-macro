SELECT
    data,
    codigo_serie,
    nome_serie,
    frequencia,
    valor,
    ingested_at
FROM sgs_series
ORDER BY codigo_serie, data
