---
title: Inflação, Trabalho & Transmissão Monetária
---

<div class="terminal-header">
  <div>
    <h1 class="terminal-title">Inflação, Trabalho & Transmissão Monetária</h1>
    <p class="terminal-subtitle">IPCA (433, 13522) · IGP-M (189) · Desocupação PNAD (24369) · Juros de Crédito (20714) · Spread (20783) · Juro Real Ex-Post vs Ex-Ante</p>
  </div>
</div>

<div class="filter-bar">
  <Dropdown name=horizonte_inf title="Horizonte Temporal" defaultValue="1825">
    <DropdownOption value="730" valueLabel="Últimos 2 anos" />
    <DropdownOption value="1825" valueLabel="Últimos 5 anos" />
    <DropdownOption value="3650" valueLabel="Últimos 10 anos" />
    <DropdownOption value="36500" valueLabel="Todo o histórico (2010+)" />
  </Dropdown>
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
  <KPITerminalCard data={inflacao_kpis} value="ipca_12m" dateCol="d13522" code="SGS 13522" title="IPCA Acum. 12m" suffix="%" decimals={2} subtitle="Meta CMN: 3,0% ±1,5 p.p." icon="percent" />
  <KPITerminalCard data={inflacao_kpis} value="ipca_mes" dateCol="d433" code="SGS 433" title="IPCA Mensal" suffix="%" decimals={2} subtitle="Variação mensal IBGE" icon="trend" />
  <KPITerminalCard data={inflacao_kpis} value="igpm_mes" dateCol="d189" code="SGS 189" title="IGP-M Mensal" suffix="%" decimals={2} subtitle="FGV · contratos/aluguéis" icon="activity" />
  <KPITerminalCard data={inflacao_kpis} value="desemprego" dateCol="d24369" code="SGS 24369" title="Desocupação (PNAD)" suffix="%" decimals={1} subtitle="Trimestre móvel IBGE" icon="users" />
  <KPITerminalCard data={inflacao_kpis} value="juros_credito" dateCol="d20714" code="SGS 20714" title="Juros Crédito SFN" suffix="%" decimals={2} subtitle="Taxa média % a.a." icon="bank" />
  <KPITerminalCard data={inflacao_kpis} value="spread_credito" dateCol="d20783" code="SGS 20783" title="Spread Bancário" suffix=" pp" decimals={2} subtitle="Spread médio operações" icon="flow" />
</div>

```sql ipca_vs_meta
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 13522
)
SELECT
    s.data,
    s.valor AS ipca_12m,
    3.0 AS meta_cmn,
    4.5 AS teto_meta
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 13522
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_inf.value}' AS INTEGER)
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
WHERE date_diff('day', j.data, l.max_data) <= CAST('${inputs.horizonte_inf.value}' AS INTEGER)
ORDER BY j.data
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">IPCA Acumulado 12m vs Meta e Teto do CMN</div>
    <div class="terminal-panel-sub">SGS 13522 (azul) vs Meta 3,0% e Teto 4,5% (cinza)</div>
    <LineChart data={ipca_vs_meta} x=data y={['ipca_12m', 'teto_meta', 'meta_cmn']} yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6', '#737373', '#525252']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=210 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Juro Real Ex-Ante (Focus) vs Ex-Post (IPCA 12m)</div>
    <div class="terminal-panel-sub">vw_juro_real_completo · % a.a. (Ex-Ante em azul, Ex-Post em cinza)</div>
    <LineChart data={juro_real_comparativo} x=data y={['juro_real_ex_ante', 'juro_real_ex_post']} yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6', '#737373']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=210 />
  </div>
</div>

```sql desemprego_serie
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 24369
)
SELECT s.data, s.valor AS taxa_desocupacao
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 24369
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_inf.value}' AS INTEGER)
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
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_inf.value}' AS INTEGER)
GROUP BY 1
ORDER BY 1
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Taxa de Desocupação — PNAD Contínua</div>
    <div class="terminal-panel-sub">SGS 24369 · % da força de trabalho</div>
    <LineChart data={desemprego_serie} x=data y=taxa_desocupacao yFmt=num1 yGridlines=false xGridlines=false colorPalette={['#3b82f6']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=200 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Transmissão Monetária — Juros de Crédito vs Spread</div>
    <div class="terminal-panel-sub">SGS 20714 (Taxa média em azul) vs SGS 20783 (Spread em cinza)</div>
    <LineChart data={transmissao_credito} x=data y={['taxa_juros_credito', 'spread_bancario']} yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6', '#737373']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=200 />
  </div>
</div>
