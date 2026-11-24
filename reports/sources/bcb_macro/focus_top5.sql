SELECT
    indicador,
    data,
    data_referencia,
    tipo_calculo,
    media,
    mediana,
    desvio_padrao,
    minimo,
    maximo,
    ingested_at
FROM focus_top5
ORDER BY indicador, data_referencia, tipo_calculo, data
