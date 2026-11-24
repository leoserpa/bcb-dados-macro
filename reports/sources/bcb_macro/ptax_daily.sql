SELECT
    data_referencia,
    moeda,
    cotacao_compra,
    cotacao_venda,
    paridade_compra,
    paridade_venda,
    tipo_boletim,
    data_hora_cotacao,
    ingested_at
FROM ptax_daily
ORDER BY moeda, data_referencia
