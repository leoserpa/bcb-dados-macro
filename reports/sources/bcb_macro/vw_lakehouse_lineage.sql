SELECT
    tabela,
    fonte,
    registros,
    data_minima,
    data_maxima,
    ultima_ingestao
FROM vw_lakehouse_lineage
ORDER BY tabela
