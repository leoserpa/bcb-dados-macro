---
title: Panorama Macro — BCB
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Panorama Macro, BCB</h1>
    <p class="page-subtitle">Resumo macroeconômico diário · 17 séries SGS, PTAX USD/EUR e Boletim Focus & Top 5</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=horizonte_overview>
        <ButtonGroupItem valueLabel="2 Anos" value="730" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
        <ButtonGroupItem valueLabel="Máx" value="36500" />
      </ButtonGroup>

      <ButtonGroup name=base_focus>
        <ButtonGroupItem valueLabel="Focus 30d" value="0" default />
        <ButtonGroupItem valueLabel="Focus 5d" value="1" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-dot"></span>Atualização útil · 09:30 BRT</span>
    </div>
  </div>
</div>

```sql kpi_sgs
SELECT
    MAX(CASE WHEN indicador_id = '432' THEN valor END) AS meta_selic,
    MAX(CASE WHEN indicador_id = '432' THEN data_observacao END) AS data_432,
    MAX(CASE WHEN indicador_id = '13522' THEN valor END) AS ipca_12m,
    MAX(CASE WHEN indicador_id = '13522' THEN data_observacao END) AS data_13522,
    MAX(CASE WHEN indicador_id = '24364' THEN valor END) AS ibc_br,
    MAX(CASE WHEN indicador_id = '24364' THEN data_observacao END) AS data_24364,
    MAX(CASE WHEN indicador_id = '13762' THEN valor END) AS dbgg_pib,
    MAX(CASE WHEN indicador_id = '13762' THEN data_observacao END) AS data_13762
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

```sql kpi_ptax
SELECT
    cotacao_venda,
    cotacao_compra,
    data_referencia
FROM bcb_macro.ptax_daily
WHERE moeda = 'USD'
ORDER BY data_referencia DESC
LIMIT 1
```

<div class="kpi-grid-5">
  <KPITerminalCard data={kpi_sgs} value="meta_selic" dateCol="data_432" title="Meta Selic Copom" suffix="%" decimals={2} subtitle="SGS 432" accent={true} />
  <KPITerminalCard data={kpi_sgs} value="ipca_12m" dateCol="data_13522" title="IPCA Acum. 12m" suffix="%" decimals={2} subtitle="Meta CMN 3,0%" accent={true} />
  <KPITerminalCard data={kpi_ptax} value="cotacao_venda" dateCol="data_referencia" title="PTAX Venda (USD)" prefix="R$ " decimals={4} subtitle="Fechamento" accent={true} />
  <KPITerminalCard data={kpi_sgs} value="ibc_br" dateCol="data_24364" title="IBC-Br Dessaz." decimals={2} subtitle="Atividade mensal" />
  <KPITerminalCard data={kpi_sgs} value="dbgg_pib" dateCol="data_13762" title="DBGG / PIB" suffix="%" decimals={2} subtitle="Dívida bruta" />
</div>

```sql selic_recente
WITH limite AS (
    SELECT MAX(data) AS max_data
    FROM bcb_macro.sgs_series
    WHERE codigo_serie = 432
)
SELECT
    s.data,
    s.valor AS meta_selic
FROM bcb_macro.sgs_series s
CROSS JOIN limite l
WHERE s.codigo_serie = 432
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_overview}' AS INTEGER)
ORDER BY s.data
```

```sql ptax_recente
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data
    FROM bcb_macro.ptax_daily
    WHERE moeda = 'USD'
),
focus_cambio AS (
    SELECT mediana_base0 AS consenso_focus
    FROM bcb_macro.vw_focus_repricing
    WHERE indicador = 'Câmbio'
      AND TRY_CAST(data_referencia AS INTEGER) = (
          SELECT YEAR(MAX(data_base0)) FROM bcb_macro.vw_focus_repricing
      )
    LIMIT 1
)
SELECT
    p.data_referencia AS data,
    p.cotacao_venda AS ptax_usd,
    f.consenso_focus
FROM bcb_macro.ptax_daily p
CROSS JOIN limite l
CROSS JOIN focus_cambio f
WHERE p.moeda = 'USD'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_overview}' AS INTEGER)
ORDER BY p.data_referencia
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Evolução da Meta Selic — Copom</div>
    <div class="terminal-panel-sub">Taxa básica definida pelo Comitê de Política Monetária (% a.a.)</div>
    <LineChart
      data={selic_recente}
      x=data
      y=meta_selic
      yFmt=num2
      step=true
      yGridlines=false
      xGridlines=false
      colorPalette={['#3b82f6']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=215
    />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">PTAX de Fechamento — USD/BRL vs Consenso Focus</div>
    <div class="terminal-panel-sub">Cotação diária de venda (azul) frente à mediana Focus anual (cinza)</div>
    <LineChart
      data={ptax_recente}
      x=data
      y={['ptax_usd', 'consenso_focus']}
      yFmt=num2
      yGridlines=false
      xGridlines=false
      colorPalette={['#3b82f6', '#737373']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=215
    />
  </div>
</div>

```sql tabela_sgs_latest
SELECT
    indicador_id AS codigo,
    indicador AS serie,
    detalhe AS frequencia,
    data_observacao AS ultima_data,
    valor
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
ORDER BY CAST(indicador_id AS INTEGER)
```

```sql focus_resumo
WITH ultimo_ano AS (
    SELECT YEAR(MAX(data_observacao)) AS ano_ref
    FROM bcb_macro.vw_macro_latest
    WHERE fonte = 'FOCUS'
)
SELECT
    v.indicador,
    v.periodo_referencia AS ano,
    v.data_observacao AS data_coleta,
    v.valor AS mediana
FROM bcb_macro.vw_macro_latest v
CROSS JOIN ultimo_ano u
WHERE v.fonte = 'FOCUS'
  AND v.detalhe LIKE concat('%base=', '${inputs.base_focus}')
  AND TRY_CAST(v.periodo_referencia AS INTEGER) BETWEEN u.ano_ref AND u.ano_ref + 3
ORDER BY v.indicador, v.periodo_referencia
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Últimas Observações — Todas as 17 Séries SGS</div>
    <div class="terminal-panel-sub">Cobertura completa de juros, inflação, atividade, crédito, fiscal e setor externo</div>
    <DataTable data={tabela_sgs_latest} rows=20>
      <Column id=codigo title="Série" />
      <Column id=serie title="Indicador" />
      <Column id=frequencia title="Freq." />
      <Column id=ultima_data title="Data" />
      <Column id=valor title="Valor" fmt=num2 />
    </DataTable>
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Consenso Boletim Focus (Base {inputs.base_focus})</div>
    <div class="terminal-panel-sub">Medianas das projeções anuais mais recentes de mercado</div>
    <DataTable data={focus_resumo} rows=16>
      <Column id=indicador title="Indicador" />
      <Column id=ano title="Ano" />
      <Column id=data_coleta title="Coleta" />
      <Column id=mediana title="Mediana" fmt=num2 />
    </DataTable>
  </div>
</div>
