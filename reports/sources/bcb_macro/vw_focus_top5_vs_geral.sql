SELECT
    indicador,
    data_referencia,
    tipo_calculo,
    data_top5,
    mediana_top5,
    mediana_geral,
    spread_top5_vs_geral,
    desvio_top5
FROM vw_focus_top5_vs_geral
ORDER BY indicador, data_referencia, tipo_calculo
