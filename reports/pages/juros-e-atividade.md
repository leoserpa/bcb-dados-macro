---
title: Juros, Atividade, Crédito & Fiscal
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Juros, Atividade Econômica, Crédito &amp; Fiscal</h1>
    <p class="page-subtitle">Política monetária, IBC-Br, dívida pública consolidada e dinâmica de crédito do Sistema Financeiro Nacional</p>
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
      <span class="status-chip">Séries SGS · Histórico desde 2010</span>
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
    MAX(CASE WHEN indicador_id = '20631' THEN valor END) AS concessoes,
    MAX(CASE WHEN indicador_id = '20631' THEN data_observacao END) AS d20631,
    MAX(CASE WHEN indicador_id = '21082' THEN valor END) AS inadimplencia,
    MAX(CASE WHEN indicador_id = '21082' THEN data_observacao END) AS d21082
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={sgs_domesticos_kpi} value="meta_selic" dateCol="d432" code="SGS 432" title="Meta Selic Copom" suffix="%" decimals={2} subtitle="Evento · % a.a." icon="bank" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="selic_diaria" dateCol="d11" code="SGS 11" title="Taxa Selic Diária" suffix="%" decimals={4} subtitle="Diária · % a.d." icon="trend" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="ibc_br" dateCol="d24364" code="SGS 24364" title="IBC-Br Dessaz." decimals={2} subtitle="Mensal · Índice" icon="activity" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="dbgg_pib" dateCol="d13762" code="SGS 13762" title="DBGG / PIB" suffix="%" decimals={2} subtitle="Mensal · % PIB" icon="percent" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="concessoes" dateCol="d20631" code="SGS 20631" title="Concessões Crédito" prefix="R$ " decimals={0} subtitle="Mensal · R$ mi" icon="dollar" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="inadimplencia" dateCol="d21082" code="SGS 21082" title="Inadimplência SFN" suffix="%" decimals={2} subtitle="Mensal · % carteira" icon="alert" />
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
    <div class="terminal-panel-title">Qual a trajetória da Meta Selic definida pelo Copom?</div>
    <div class="terminal-panel-sub">SGS 432 · Taxa básica (% a.a.) em escada</div>
    <TerminalLineChart data={selic_meta} x="data" y="meta_selic" labels={['Meta Selic']} suffix="%" decimals={2} step={true} height="240px" />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como evolui a dívida bruta (DBGG) frente à líquida (DLSP)?</div>
    <div class="terminal-panel-sub">DBGG/PIB (laranja) vs DLSP/PIB (cinza) · % do PIB</div>
    <TerminalLineChart data={dbgg_pib} x="data" y={['dbgg_pib', 'dlsp_pib']} labels={['DBGG / PIB', 'DLSP / PIB']} colors={['#ff6b00', '#737373']} suffix="%" decimals={2} height="240px" />
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

<div class="terminal-grid-3">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como está o ritmo da atividade (IBC-Br)?</div>
    <div class="terminal-panel-sub">SGS 24364 · Índice com ajuste sazonal</div>
    <TerminalLineChart data={ibc_br} x="data" y="ibc_br" labels={['IBC-Br']} decimals={2} height="230px" />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual o resultado primário em 12 meses?</div>
    <div class="terminal-panel-sub">SGS 5793 · Setor público consolidado (% PIB)</div>
    <BarChart data={primario_12m} x=data y=resultado_primario_pib yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#ff6b00']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=200 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual o volume mensal de concessões?</div>
    <div class="terminal-panel-sub">SGS 20631 · Novas operações (R$ milhões)</div>
    <BarChart data={concessoes_credito} x=data y=concessoes_r_mi yFmt=num0 yGridlines=false xGridlines=false colorPalette={['#737373']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=200 />
  </div>
</div>

```sql selic_diaria
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 11
)
SELECT s.data, s.valor AS selic_diaria
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 11
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

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como se comporta a Taxa Selic efetiva diária?</div>
    <div class="terminal-panel-sub">SGS 11 · Taxa overnight (% ao dia)</div>
    <TerminalLineChart data={selic_diaria} x="data" y="selic_diaria" labels={['Selic Diária']} colors={['#a6a6a6']} suffix="%" decimals={4} height="230px" />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">A inadimplência do SFN está pressionando a carteira?</div>
    <div class="terminal-panel-sub">SGS 21082 · Atrasos acima de 90 dias (% da carteira)</div>
    <TerminalLineChart data={inadimplencia_sfn} x="data" y="inadimplencia_pct" labels={['Inadimplência SFN']} suffix="%" decimals={2} height="230px" />
  </div>
</div>
