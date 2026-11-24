---
title: Panorama Macroeconômico — Banco Central do Brasil
---

<div class="terminal-header">
  <div>
    <h1 class="terminal-title">Panorama Macroeconômico — Banco Central do Brasil</h1>
    <p class="terminal-subtitle">Camada Gold · SGS (9 séries) + PTAX USD (4.241 dias) + Focus OData (122.217 obs.)</p>
  </div>
  <div class="status-pills">
    <span class="status-pill"><span class="status-dot"></span>Gold: bcb_macro.duckdb</span>
    <span class="status-pill"><span class="status-dot"></span>23/23 Quality Gates OK</span>
  </div>
</div>

<div class="filter-bar">
  <Dropdown name=horizonte_overview title="Período" defaultValue="1825">
    <DropdownOption value="730" valueLabel="Últimos 2 anos" />
    <DropdownOption value="1825" valueLabel="Últimos 5 anos" />
    <DropdownOption value="3650" valueLabel="Últimos 10 anos" />
    <DropdownOption value="36500" valueLabel="Todo o histórico (2010+)" />
  </Dropdown>

  <Dropdown name=base_focus title="Base Focus" defaultValue="0">
    <DropdownOption value="0" valueLabel="Base 0 — Últimos 30 dias" />
    <DropdownOption value="1" valueLabel="Base 1 — Últimos 5 dias úteis" />
  </Dropdown>
</div>

```sql kpi_sgs
SELECT
    MAX(CASE WHEN indicador_id = '432' THEN valor END) AS meta_selic,
    MAX(CASE WHEN indicador_id = '432' THEN data_observacao END) AS data_432,
    MAX(CASE WHEN indicador_id = '11' THEN valor END) AS selic_diaria,
    MAX(CASE WHEN indicador_id = '11' THEN data_observacao END) AS data_11,
    MAX(CASE WHEN indicador_id = '24364' THEN valor END) AS ibc_br,
    MAX(CASE WHEN indicador_id = '24364' THEN data_observacao END) AS data_24364,
    MAX(CASE WHEN indicador_id = '13762' THEN valor END) AS dbgg_pib,
    MAX(CASE WHEN indicador_id = '13762' THEN data_observacao END) AS data_13762,
    MAX(CASE WHEN indicador_id = '20631' THEN valor END) AS concessoes_credito,
    MAX(CASE WHEN indicador_id = '20631' THEN data_observacao END) AS data_20631,
    MAX(CASE WHEN indicador_id = '21082' THEN valor END) AS inadimplencia,
    MAX(CASE WHEN indicador_id = '21082' THEN data_observacao END) AS data_21082,
    MAX(CASE WHEN indicador_id = '13982' THEN valor END) AS reservas_usd_mi,
    MAX(CASE WHEN indicador_id = '13982' THEN data_observacao END) AS data_13982,
    MAX(CASE WHEN indicador_id = '13967' THEN valor END) AS fluxo_comercial,
    MAX(CASE WHEN indicador_id = '13967' THEN data_observacao END) AS data_13967,
    MAX(CASE WHEN indicador_id = '13970' THEN valor END) AS fluxo_financeiro,
    MAX(CASE WHEN indicador_id = '13970' THEN data_observacao END) AS data_13970
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

```sql kpi_ptax
SELECT
    cotacao_venda,
    cotacao_compra,
    data_referencia,
    tipo_boletim
FROM bcb_macro.ptax_daily
WHERE moeda = 'USD'
ORDER BY data_referencia DESC
LIMIT 1
```

<div class="section-kicker">Cobertura Completa — Todas as 9 Séries SGS + PTAX Fechamento</div>

<div class="kpi-grid-5">
  <KPITerminalCard data={kpi_sgs} value="meta_selic" dateCol="data_432" code="SGS 432" title="Meta Selic Copom" suffix="%" decimals={2} subtitle="Evento · % a.a." icon="percent" />
  <KPITerminalCard data={kpi_sgs} value="selic_diaria" dateCol="data_11" code="SGS 11" title="Taxa Selic Diária" suffix="%" decimals={4} subtitle="Diária · % ao dia" icon="trend" />
  <KPITerminalCard data={kpi_ptax} value="cotacao_venda" dateCol="data_referencia" code="PTAX USD" title="PTAX Venda (Fech.)" prefix="R$ " decimals={4} subtitle="Boletim Fechamento" icon="dollar" />
  <KPITerminalCard data={kpi_sgs} value="ibc_br" dateCol="data_24364" code="SGS 24364" title="IBC-Br Dessaz." decimals={2} subtitle="Mensal · Índice" icon="activity" />
  <KPITerminalCard data={kpi_sgs} value="dbgg_pib" dateCol="data_13762" code="SGS 13762" title="DBGG / PIB" suffix="%" decimals={2} subtitle="Mensal · % do PIB" icon="bank" />
  <KPITerminalCard data={kpi_sgs} value="concessoes_credito" dateCol="data_20631" code="SGS 20631" title="Concessões Crédito" prefix="R$ " decimals={0} subtitle="Mensal · R$ milhões" icon="dollar" />
  <KPITerminalCard data={kpi_sgs} value="inadimplencia" dateCol="data_21082" code="SGS 21082" title="Inadimplência SFN" suffix="%" decimals={2} subtitle="Mensal · % carteira" icon="alert" />
  <KPITerminalCard data={kpi_sgs} value="reservas_usd_mi" dateCol="data_13982" code="SGS 13982" title="Reservas Internac." prefix="$ " decimals={0} subtitle="Diária · US$ milhões" icon="globe" />
  <KPITerminalCard data={kpi_sgs} value="fluxo_comercial" dateCol="data_13967" code="SGS 13967" title="Fluxo Comercial" prefix="$ " decimals={2} signed={true} subtitle="Diária · US$ milhões" icon="flow" />
  <KPITerminalCard data={kpi_sgs} value="fluxo_financeiro" dateCol="data_13970" code="SGS 13970" title="Fluxo Financeiro" prefix="$ " decimals={2} signed={true} subtitle="Diária · US$ milhões" icon="flow" />
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
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_overview.value}' AS INTEGER)
ORDER BY s.data
```

```sql ptax_recente
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data
    FROM bcb_macro.ptax_daily
    WHERE moeda = 'USD'
)
SELECT
    p.data_referencia AS data,
    p.cotacao_venda
FROM bcb_macro.ptax_daily p
CROSS JOIN limite l
WHERE p.moeda = 'USD'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_overview.value}' AS INTEGER)
ORDER BY p.data_referencia
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Evolução da Meta Selic — ciclos de política monetária</div>
    <div class="terminal-panel-sub">bcb_macro.sgs_series · codigo_serie = 432 · % a.a.</div>
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
      chartAreaHeight=210
    />
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Evolução da PTAX de fechamento — USD/BRL</div>
    <div class="terminal-panel-sub">bcb_macro.ptax_daily · moeda = 'USD'</div>
    <LineChart
      data={ptax_recente}
      x=data
      y=cotacao_venda
      yFmt=num2
      yGridlines=false
      xGridlines=false
      colorPalette={['#3b82f6']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=210
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
  AND v.detalhe LIKE concat('%base=', '${inputs.base_focus.value}')
  AND TRY_CAST(v.periodo_referencia AS INTEGER) BETWEEN u.ano_ref AND u.ano_ref + 3
ORDER BY v.indicador, v.periodo_referencia
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Últimas Observações — Todas as 9 Séries SGS</div>
    <div class="terminal-panel-sub">vw_macro_latest WHERE fonte = 'SGS'</div>
    <DataTable data={tabela_sgs_latest} rows=10>
      <Column id=codigo title="Cod" />
      <Column id=serie title="Indicador" />
      <Column id=frequencia title="Freq" />
      <Column id=ultima_data title="Data" />
      <Column id=valor title="Valor" fmt=num2 />
    </DataTable>
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Consenso Boletim Focus (Base {inputs.base_focus.value})</div>
    <div class="terminal-panel-sub">vw_macro_latest WHERE fonte = 'FOCUS'</div>
    <DataTable data={focus_resumo} rows=16>
      <Column id=indicador title="Indicador" />
      <Column id=ano title="Ano" />
      <Column id=data_coleta title="Coleta" />
      <Column id=mediana title="Mediana" fmt=num2 />
    </DataTable>
  </div>
</div>
