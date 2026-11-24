SELECT
    indicador,
    indicador_detalhe,
    data,
    data_referencia,
    media,
    mediana,
    desvio_padrao,
    minimo,
    maximo,
    numero_respondentes,
    base_calculo,
    ingested_at
FROM focus_expectations
ORDER BY indicador, data_referencia, data
