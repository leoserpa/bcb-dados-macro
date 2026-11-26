---
title: Inflação, Trabalho & Transmissão Monetária
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Inflação, Mercado de Trabalho &amp; Transmissão Monetária</h1>
    <p class="page-subtitle">IPCA, IGP-M, desocupação PNAD, custo de crédito bancário e juro real ex-ante vs ex-post</p>
  </div>

  <div class="controls-bar">
    <FilterBar defaults={{ horizonte_inf: '1825' }}>
      <ButtonGroup name=horizonte_inf>
        <ButtonGroupItem valueLabel="2 Anos" value="730" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>
    </FilterBar>

    <div class="controls-right">
      <span class="status-chip">Janela · {inputs.horizonte_inf === '730' ? '2 Anos' : inputs.horizonte_inf === '1825' ? '5 Anos' : inputs.horizonte_inf === '3650' ? '10 Anos' : 'Máx'} · Meta CMN <span class="status-chip-accent">3,0% ± 1,5 pp</span></span>
    </div>
  </div>
</div>

```sql inflacao_kpis
SELECT
    MAX(CASE WHEN indicador_id = '13522' THEN valor END) AS ipca_12m,
    MAX(CASE WHEN indicador_id = '13522' THEN data_observacao END) AS d13522,
    MAX(CASE WHEN indicador_id = '433' THEN valor END) AS ipca_mes,
    MAX(CASE WHEN indicador_id = '433' THEN data_observacao END) AS d433,
    MAX(CASE WHEN indicador_id = '189' THEN valor END) AS igpm_mes,
    MAX(CASE WHEN indicador_id = '189' THEN data_observacao END) AS d189,
    MAX(CASE WHEN indicador_id = '24369' THEN valor END) AS desemprego,
    MAX(CASE WHEN indicador_id = '24369' THEN data_observacao END) AS d24369,
    MAX(CASE WHEN indicador_id = '20714' THEN valor END) AS juros_credito,
    MAX(CASE WHEN indicador_id = '20714' THEN data_observacao END) AS d20714,
    MAX(CASE WHEN indicador_id = '20783' THEN valor END) AS spread_credito,
    MAX(CASE WHEN indicador_id = '20783' THEN data_observacao END) AS d20783
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={inflacao_kpis} value="ipca_12m" dateCol="d13522" code="SGS 13522" title="IPCA Acum. 12m" suffix="%" decimals={2} subtitle="Teto 4,50%" icon="percent" />
  <KPITerminalCard data={inflacao_kpis} value="ipca_mes" dateCol="d433" code="SGS 433" title="IPCA Mensal" suffix="%" decimals={2} subtitle="IBGE mensal" icon="trend" />
  <KPITerminalCard data={inflacao_kpis} value="igpm_mes" dateCol="d189" code="SGS 189" title="IGP-M Mensal" suffix="%" decimals={2} subtitle="FGV mensal" icon="activity" />
  <KPITerminalCard data={inflacao_kpis} value="desemprego" dateCol="d24369" code="SGS 24369" title="Desocupação (PNAD)" suffix="%" decimals={1} subtitle="PNAD IBGE" icon="users" />
  <KPITerminalCard data={inflacao_kpis} value="juros_credito" dateCol="d20714" code="SGS 20714" title="Juros Crédito SFN" suffix="%" decimals={2} subtitle="Média % a.a." icon="bank" />
  <KPITerminalCard data={inflacao_kpis} value="spread_credito" dateCol="d20783" code="SGS 20783" title="Spread Bancário" suffix=" pp" decimals={2} subtitle="Spread médio" icon="flow" />
</div>

```sql ipca_vs_meta
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 13522
)
SELECT
    s.data,
    s.valor AS ipca_12m,
    4.5 AS teto_meta,
    3.0 AS meta_cmn
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 13522
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_inf}' AS INTEGER)
ORDER BY s.data
```

```sql juro_real_comparativo
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.vw_juro_real_completo
)
SELECT
    j.data,
    j.juro_real_ex_ante,
    j.juro_real_ex_post
FROM bcb_macro.vw_juro_real_completo j CROSS JOIN limite l
WHERE date_diff('day', j.data, l.max_data) <= CAST('${inputs.horizonte_inf}' AS INTEGER)
ORDER BY j.data
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">O IPCA 12m está acima do teto da meta do CMN?</div>
    <div class="terminal-panel-sub">SGS 13522 (laranja) vs teto 4,5% e centro 3,0% (cinza)</div>
    <TerminalLineChart data={ipca_vs_meta} x="data" y={['ipca_12m', 'teto_meta', 'meta_cmn']} labels={['IPCA 12m', 'Teto 4,5%', 'Meta 3,0%']} colors={['#ff6b00', '#737373', '#525252']} dashedIndices={[1, 2]} suffix="%" decimals={2} height="245px" />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual a distância entre Juro Real Ex-Ante e Ex-Post?</div>
    <div class="terminal-panel-sub">Ex-Ante via IPCA Focus (laranja) vs Ex-Post via IPCA 12m realizado (cinza) · % a.a.</div>
    <TerminalLineChart data={juro_real_comparativo} x="data" y={['juro_real_ex_ante', 'juro_real_ex_post']} labels={['Juro Real Ex-Ante', 'Juro Real Ex-Post']} colors={['#ff6b00', '#737373']} suffix="%" decimals={2} height="245px" />
  </div>
</div>

```sql desemprego_serie
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 24369
)
SELECT s.data, s.valor AS taxa_desocupacao
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 24369
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_inf}' AS INTEGER)
ORDER BY s.data
```

```sql transmissao_credito
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie IN (20714, 20783)
)
SELECT
    s.data,
    MAX(CASE WHEN s.codigo_serie = 20714 THEN s.valor END) AS taxa_juros_credito,
    MAX(CASE WHEN s.codigo_serie = 20783 THEN s.valor END) AS spread_bancario
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie IN (20714, 20783)
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_inf}' AS INTEGER)
GROUP BY 1
ORDER BY 1
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como evoluiu a taxa de desocupação (PNAD Contínua)?</div>
    <div class="terminal-panel-sub">SGS 24369 · Percentual da força de trabalho</div>
    <TerminalLineChart data={desemprego_serie} x="data" y="taxa_desocupacao" labels={['Desocupação PNAD']} suffix="%" decimals={1} height="240px" />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como a política monetária se transmite ao crédito?</div>
    <div class="terminal-panel-sub">Taxa média de juros do crédito (laranja) vs spread bancário (cinza) · % a.a. / p.p.</div>
    <TerminalLineChart data={transmissao_credito} x="data" y={['taxa_juros_credito', 'spread_bancario']} labels={['Juros Crédito', 'Spread Bancário']} colors={['#ff6b00', '#737373']} suffix="%" decimals={2} height="240px" />
  </div>
</div>
