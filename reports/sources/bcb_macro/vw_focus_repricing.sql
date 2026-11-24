SELECT
    indicador,
    data_referencia,
    data_base0,
    mediana_base0,
    mediana_base1,
    repricing_b1_vs_b0,
    drift_30d,
    desvio_padrao,
    numero_respondentes
FROM vw_focus_repricing
ORDER BY indicador, data_referencia
