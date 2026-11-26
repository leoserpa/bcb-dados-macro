---
title: Câmbio (PTAX) & Setor Externo
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Câmbio (PTAX) &amp; Setor Externo</h1>
    <p class="page-subtitle">Cotações diárias USD e EUR priorizando fechamento · Reservas internacionais · Fluxos cambiais</p>
  </div>

  <div class="controls-bar">
    <FilterBar defaults={{ moeda_ptax: 'USD', horizonte_cambio: '1825' }}>
      <ButtonGroup name=moeda_ptax>
        <ButtonGroupItem valueLabel="USD — Dólar" value="USD" default />
        <ButtonGroupItem valueLabel="EUR — Euro" value="EUR" />
      </ButtonGroup>

      <ButtonGroup name=horizonte_cambio>
        <ButtonGroupItem valueLabel="1 Ano" value="365" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>
    </FilterBar>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">{inputs.moeda_ptax}/BRL</span><span class="status-chip-sep" aria-hidden="true">/</span>{inputs.horizonte_cambio === '365' ? '1 Ano' : inputs.horizonte_cambio === '1825' ? '5 Anos' : inputs.horizonte_cambio === '3650' ? '10 Anos' : 'Máx'}</span>
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
    MAX(CASE WHEN indicador_id = '13982' THEN valor / 1000.0 END) AS reservas_usd_bi,
    MAX(CASE WHEN indicador_id = '13982' THEN data_observacao END) AS d13982,
    MAX(CASE WHEN indicador_id = '13967' THEN valor END) AS fluxo_com,
    MAX(CASE WHEN indicador_id = '13967' THEN data_observacao END) AS d13967,
    MAX(CASE WHEN indicador_id = '13970' THEN valor END) AS fluxo_fin,
    MAX(CASE WHEN indicador_id = '13970' THEN data_observacao END) AS d13970
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={ptax_ultima} value="cotacao_compra" dateCol="data_referencia" code="PTAX COMPRA" title={'Cotação Compra (' + inputs.moeda_ptax + ')'} prefix="R$ " decimals={4} subtitle="Fechamento" icon="dollar" />
  <KPITerminalCard data={ptax_ultima} value="cotacao_venda" dateCol="data_referencia" code="PTAX VENDA" title={'Cotação Venda (' + inputs.moeda_ptax + ')'} prefix="R$ " decimals={4} subtitle="Fechamento" icon="dollar" />
  <KPITerminalCard data={ptax_ultima} value="spread" dateCol="data_referencia" code="SPREAD" title={'Spread (' + inputs.moeda_ptax + ')'} prefix="R$ " decimals={4} subtitle="Venda − compra" icon="flow" />
  <KPITerminalCard data={externo_sgs} value="reservas_usd_bi" dateCol="d13982" code="SGS 13982" title="Reservas Internac." prefix="US$ " suffix=" bi" decimals={1} subtitle="Conceito liquidez" icon="globe" />
  <KPITerminalCard data={externo_sgs} value="fluxo_com" dateCol="d13967" code="SGS 13967" title="Fluxo Comercial" prefix="US$ " suffix=" mi" decimals={0} signed={true} subtitle="Fluxo diário" icon="flow" />
  <KPITerminalCard data={externo_sgs} value="fluxo_fin" dateCol="d13970" code="SGS 13970" title="Fluxo Financeiro" prefix="US$ " suffix=" mi" decimals={0} signed={true} subtitle="Fluxo diário" icon="flow" />
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
    tipo_boletim,
    cotacao_compra,
    cotacao_venda,
    cotacao_venda - cotacao_compra AS spread
FROM bcb_macro.ptax_daily
WHERE moeda = '${inputs.moeda_ptax}'
ORDER BY data_referencia DESC
LIMIT 10
```

<div class="terminal-grid-asym">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como evoluiu a PTAX de fechamento ({inputs.moeda_ptax}/BRL)?</div>
    <div class="terminal-panel-sub">Taxa oficial de venda {inputs.moeda_ptax}/BRL publicada pelo Banco Central · priorizando fechamento</div>
    <TerminalLineChart
      data={ptax_historico}
      x="data"
      y="cotacao_venda"
      labels={['PTAX Venda (' + inputs.moeda_ptax + ')']}
      prefix="R$ "
      decimals={2}
      height="325px"
    />
  </div>

  <ConditionalTable
    data={ptax_tabela}
    title="Últimos Boletins PTAX ({inputs.moeda_ptax})"
    subtitle="10 observações mais recentes com spread compra/venda"
    minWidth="420px"
    columns={[
      { key: 'data', label: 'Data', format: 'date', emphasis: 'muted' },
      { key: 'tipo_boletim', label: 'Boletim', format: 'text', emphasis: 'muted' },
      { key: 'cotacao_compra', label: 'Compra', align: 'right', format: 'brl4', emphasis: 'muted' },
      { key: 'cotacao_venda', label: 'Venda', align: 'right', format: 'brl4', emphasis: 'primary' },
      { key: 'spread', label: 'Spread', align: 'right', format: 'brl4', emphasis: 'muted' }
    ]}
  />
</div>

```sql reservas_serie
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 13982
)
SELECT s.data, s.valor / 1000.0 AS reservas_usd_bi
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
    SUM(s.valor) / 1000.0 AS fluxo_usd_bi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie IN (13967, 13970)
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_cambio}' AS INTEGER)
GROUP BY 1, 2
ORDER BY 1, 2
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual o nível atual das Reservas Internacionais?</div>
    <div class="terminal-panel-sub">SGS 13982 · Colchão de liquidez externa (US$ bilhões)</div>
    <TerminalLineChart
      data={reservas_serie}
      x="data"
      y="reservas_usd_bi"
      labels={['Reservas Internacionais']}
      colors={['#a6a6a6']}
      prefix="US$ "
      suffix=" bi"
      decimals={1}
      height="240px"
    />
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual o balanço mensal entre Fluxo Comercial e Financeiro?</div>
    <div class="terminal-panel-sub">Comercial (laranja) vs Financeiro (cinza) · consolidado mensal em US$ bilhões</div>
    <BarChart
      data={fluxo_cambial_mensal}
      x=mes
      y=fluxo_usd_bi
      series=segmento
      yFmt=num1
      type=grouped
      yGridlines=false
      xGridlines=false
      colorPalette={['#ff6b00', '#525252']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=210
    />
  </div>
</div>
