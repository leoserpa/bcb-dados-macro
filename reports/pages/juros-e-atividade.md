---
title: Juros, Atividade, Crédito & Fiscal
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Juros, Atividade, Crédito & Fiscal</h1>
    <p class="page-subtitle">Política monetária, IBC-Br dessazonalizado, endividamento público (DBGG e DLSP), resultado primário e crédito SFN</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=horizonte>
        <ButtonGroupItem valueLabel="2 Anos" value="730" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>
    </div>
    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-dot"></span>8 séries domésticas SGS</span>
    </div>
  </div>
</div>

```sql sgs_domesticos_kpi
SELECT
    MAX(CASE WHEN indicador_id = '432' THEN valor END) AS meta_selic,
    MAX(CASE WHEN indicador_id = '432' THEN data_observacao END) AS d432,
    MAX(CASE WHEN indicador_id = '11' THEN valor END) AS selic_diaria,
    MAX(CASE WHEN indicador_id = '11' THEN data_observacao END) AS d11,
    MAX(CASE WHEN indicador_id = '24364' THEN valor END) AS ibc_br,
    MAX(CASE WHEN indicador_id = '24364' THEN data_observacao END) AS d24364,
    MAX(CASE WHEN indicador_id = '13762' THEN valor END) AS dbgg_pib,
    MAX(CASE WHEN indicador_id = '13762' THEN data_observacao END) AS d13762,
    MAX(CASE WHEN indicador_id = '5793' THEN valor END) AS primario_pib,
    MAX(CASE WHEN indicador_id = '5793' THEN data_observacao END) AS d5793,
    MAX(CASE WHEN indicador_id = '21082' THEN valor END) AS inadimplencia,
    MAX(CASE WHEN indicador_id = '21082' THEN data_observacao END) AS d21082
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={sgs_domesticos_kpi} value="meta_selic" dateCol="d432" title="Meta Selic Copom" suffix="%" decimals={2} subtitle="% a.a." accent={true} />
  <KPITerminalCard data={sgs_domesticos_kpi} value="selic_diaria" dateCol="d11" title="Taxa Selic Diária" suffix="%" decimals={4} subtitle="% ao dia" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="ibc_br" dateCol="d24364" title="IBC-Br Dessaz." decimals={2} subtitle="Índice mensal" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="dbgg_pib" dateCol="d13762" title="DBGG / PIB" suffix="%" decimals={2} subtitle="Dívida bruta" accent={true} />
  <KPITerminalCard data={sgs_domesticos_kpi} value="primario_pib" dateCol="d5793" title="Primário 12m / PIB" suffix="%" decimals={2} signed={true} subtitle="Setor público" accent={true} />
  <KPITerminalCard data={sgs_domesticos_kpi} value="inadimplencia" dateCol="d21082" title="Inadimplência SFN" suffix="%" decimals={2} subtitle="% da carteira" />
</div>

```sql selic_meta
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 432
)
SELECT s.data, s.valor AS meta_selic
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 432
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte}' AS INTEGER)
ORDER BY s.data
```

```sql dbgg_pib
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie IN (13762, 4513)
)
SELECT
    s.data,
    MAX(CASE WHEN s.codigo_serie = 13762 THEN s.valor END) AS dbgg_pib,
    MAX(CASE WHEN s.codigo_serie = 4513 THEN s.valor END) AS dlsp_pib
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie IN (13762, 4513)
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte}' AS INTEGER)
GROUP BY 1
ORDER BY 1
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Trajetória da Meta Selic — Copom</div>
    <div class="terminal-panel-sub">Ciclos de aperto e afrouxamento monetário (% a.a.)</div>
    <LineChart data={selic_meta} x=data y=meta_selic yFmt=num2 step=true yGridlines=false xGridlines=false colorPalette={['#3b82f6']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=205 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Trajetória Fiscal — DBGG/PIB vs DLSP/PIB</div>
    <div class="terminal-panel-sub">Dívida Bruta (azul) frente à Dívida Líquida do Setor Público (cinza) · % do PIB</div>
    <LineChart data={dbgg_pib} x=data y={['dbgg_pib', 'dlsp_pib']} yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6', '#737373']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=205 />
  </div>
</div>

```sql ibc_br
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 24364
)
SELECT s.data, s.valor AS ibc_br
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 24364
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte}' AS INTEGER)
ORDER BY s.data
```

```sql primario_12m
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 5793
)
SELECT s.data, s.valor AS resultado_primario_pib
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 5793
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte}' AS INTEGER)
ORDER BY s.data
```

```sql concessoes_credito
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 20631
)
SELECT s.data, s.valor AS concessoes_r_mi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 20631
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte}' AS INTEGER)
ORDER BY s.data
```

```sql inadimplencia_sfn
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 21082
)
SELECT s.data, s.valor AS inadimplencia_pct
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 21082
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte}' AS INTEGER)
ORDER BY s.data
```

<div class="terminal-grid-3">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Atividade Econômica — IBC-Br</div>
    <div class="terminal-panel-sub">Índice dessazonalizado (prévia mensal do PIB)</div>
    <LineChart data={ibc_br} x=data y=ibc_br yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#a3a3a3']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=190 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Resultado Primário 12m (% PIB)</div>
    <div class="terminal-panel-sub">Superávit / déficit do setor público consolidado</div>
    <BarChart data={primario_12m} x=data y=resultado_primario_pib yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=190 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Concessões de Crédito SFN</div>
    <div class="terminal-panel-sub">Volume mensal de novas operações (R$ milhões)</div>
    <BarChart data={concessoes_credito} x=data y=concessoes_r_mi yFmt=num0 yGridlines=false xGridlines=false colorPalette={['#525252']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=190 />
  </div>
</div>

<div class="terminal-panel">
  <div class="terminal-panel-title">Evolução da Inadimplência Total do SFN</div>
  <div class="terminal-panel-sub">Percentual da carteira total com atraso superior a 90 dias (%)</div>
  <LineChart data={inadimplencia_sfn} x=data y=inadimplencia_pct yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=185 />
</div>
