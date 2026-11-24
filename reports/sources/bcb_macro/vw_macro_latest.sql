SELECT
    fonte,
    indicador_id,
    indicador,
    data_observacao,
    periodo_referencia,
    metrica,
    valor,
    detalhe,
    ingested_at
FROM vw_macro_latest
