---
title: Câmbio (PTAX) & Setor Externo
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Câmbio (PTAX) & Setor Externo</h1>
    <p class="page-subtitle">Cotações diárias de fechamento (USD e EUR), reservas internacionais e fluxo cambial contratado</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=moeda_ptax>
        <ButtonGroupItem valueLabel="PTAX USD" value="USD" default />
        <ButtonGroupItem valueLabel="PTAX EUR" value="EUR" />
      </ButtonGroup>

      <ButtonGroup name=horizonte_cambio>
        <ButtonGroupItem valueLabel="1 Ano" value="365" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-dot"></span>Moeda ativa: {inputs.moeda_ptax}</span>
    </div>
  </div>
</div>

```sql ptax_ultima
SELECT
    data_referencia,
    cotacao_compra,
    cotacao_venda,
    cotacao_venda - cotacao_compra AS spread,
    tipo_boletim
FROM bcb_macro.ptax_daily
WHERE moeda = '${inputs.moeda_ptax}'
ORDER BY data_referencia DESC
LIMIT 1
```

```sql externo_sgs
SELECT
    MAX(CASE WHEN indicador_id = '13982' THEN valor END) AS reservas_usd_mi,
    MAX(CASE WHEN indicador_id = '13982' THEN data_observacao END) AS d13982,
    MAX(CASE WHEN indicador_id = '13967' THEN valor END) AS fluxo_com,
    MAX(CASE WHEN indicador_id = '13967' THEN data_observacao END) AS d13967,
    MAX(CASE WHEN indicador_id = '13970' THEN valor END) AS fluxo_fin,
    MAX(CASE WHEN indicador_id = '13970' THEN data_observacao END) AS d13970
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={ptax_ultima} value="cotacao_compra" dateCol="data_referencia" title="PTAX Compra" prefix="R$ " decimals={4} subtitle="Fechamento" />
  <KPITerminalCard data={ptax_ultima} value="cotacao_venda" dateCol="data_referencia" title="PTAX Venda" prefix="R$ " decimals={4} subtitle="Fechamento" accent={true} />
  <KPITerminalCard data={ptax_ultima} value="spread" dateCol="data_referencia" title="Spread Compra/Venda" prefix="R$ " decimals={4} subtitle="Venda menos compra" />
  <KPITerminalCard data={externo_sgs} value="reservas_usd_mi" dateCol="d13982" title="Reservas Internac." prefix="$ " decimals={0} subtitle="US$ milhões" accent={true} />
  <KPITerminalCard data={externo_sgs} value="fluxo_com" dateCol="d13967" title="Fluxo Comercial" prefix="$ " decimals={2} signed={true} subtitle="US$ mi · diário" />
  <KPITerminalCard data={externo_sgs} value="fluxo_fin" dateCol="d13970" title="Fluxo Financeiro" prefix="$ " decimals={2} signed={true} subtitle="US$ mi · diário" accent={true} />
</div>

```sql ptax_historico
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data
    FROM bcb_macro.ptax_daily
    WHERE moeda = '${inputs.moeda_ptax}'
)
SELECT
    p.data_referencia AS data,
    p.cotacao_venda
FROM bcb_macro.ptax_daily p
CROSS JOIN limite l
WHERE p.moeda = '${inputs.moeda_ptax}'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_cambio}' AS INTEGER)
ORDER BY p.data_referencia
```

```sql ptax_tabela
SELECT
    data_referencia AS data,
    moeda,
    cotacao_compra,
    cotacao_venda,
    cotacao_venda - cotacao_compra AS spread
FROM bcb_macro.ptax_daily
WHERE moeda = '${inputs.moeda_ptax}'
ORDER BY data_referencia DESC
LIMIT 20
```

<div class="terminal-grid-asym">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Evolução Histórica da PTAX de Fechamento — {inputs.moeda_ptax}/BRL</div>
    <div class="terminal-panel-sub">Cotação diária de venda priorizando o boletim de fechamento do Banco Central</div>
    <LineChart data={ptax_historico} x=data y=cotacao_venda yFmt=num2 yGridlines=false xGridlines=false colorPalette={['#3b82f6']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=255 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Últimos Boletins PTAX ({inputs.moeda_ptax})</div>
    <div class="terminal-panel-sub">Fechamentos diários recentes</div>
    <DataTable data={ptax_tabela} rows=8>
      <Column id=data title="Data" />
      <Column id=cotacao_compra title="Compra" fmt=num4 />
      <Column id=cotacao_venda title="Venda" fmt=num4 />
      <Column id=spread title="Spread" fmt=num4 />
    </DataTable>
  </div>
</div>

```sql reservas_serie
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 13982
)
SELECT s.data, s.valor AS reservas_usd_mi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 13982
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_cambio}' AS INTEGER)
ORDER BY s.data
```

```sql fluxo_cambial_mensal
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie IN (13967, 13970)
)
SELECT
    date_trunc('month', s.data) AS mes,
    s.nome_serie AS segmento,
    SUM(s.valor) AS fluxo_usd_mi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie IN (13967, 13970)
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_cambio}' AS INTEGER)
GROUP BY 1, 2
ORDER BY 1, 2
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Reservas Internacionais — Colchão Externo</div>
    <div class="terminal-panel-sub">Posição diária das reservas brasileiras (US$ milhões)</div>
    <LineChart data={reservas_serie} x=data y=reservas_usd_mi yFmt=num0 yGridlines=false xGridlines=false colorPalette={['#a3a3a3']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=200 />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Fluxo Cambial Mensal — Comercial vs Financeiro</div>
    <div class="terminal-panel-sub">Saldo líquido mensal contratado (US$ milhões)</div>
    <BarChart data={fluxo_cambial_mensal} x=mes y=fluxo_usd_mi series=segmento yFmt=num0 type=grouped yGridlines=false xGridlines=false colorPalette={['#3b82f6', '#525252']} echartsOptions={{ backgroundColor: 'transparent' }} chartAreaHeight=200 />
  </div>
</div>
