SELECT
    data,
    selic_meta,
    ipca_12m_realizado,
    ipca_focus_ano,
    juro_real_ex_post,
    juro_real_ex_ante
FROM vw_juro_real_completo
ORDER BY data
