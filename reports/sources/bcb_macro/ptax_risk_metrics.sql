SELECT
    data_referencia,
    moeda,
    cotacao_compra,
    cotacao_venda,
    spread,
    retorno_diario_pct,
    media_movel_21d,
    media_movel_252d,
    vol_anualizada_21d,
    zscore_252d
FROM ptax_risk_metrics
ORDER BY moeda, data_referencia
