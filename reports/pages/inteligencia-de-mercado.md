---
title: Inteligência de Mercado, Regimes & Simulador
---

<div class="terminal-header">
  <div>
    <h1 class="terminal-title">Inteligência de Mercado, Regimes & Simulador</h1>
    <p class="terminal-subtitle">Motor analítico Gold: Juro Real Ex-Ante · Repricing Focus (5d vs 30d) · Volatilidade & Z-Score PTAX · Cenários</p>
  </div>
  <div class="status-pills">
    <span class="status-pill"><span class="status-dot"></span>DuckDB-WASM Live</span>
  </div>
</div>

<div class="filter-bar">
  <Dropdown name=horizonte_intel title="Horizonte" defaultValue="1825">
    <DropdownOption value="730" valueLabel="Últimos 2 anos" />
    <DropdownOption value="1825" valueLabel="Últimos 5 anos" />
    <DropdownOption value="3650" valueLabel="Últimos 10 anos" />
  </Dropdown>

  <Dropdown name=choque_selic title="Choque Selic" defaultValue="0">
    <DropdownOption value="-1.0" valueLabel="-1,00 p.p." />
    <DropdownOption value="-0.5" valueLabel="-0,50 p.p." />
    <DropdownOption value="0" valueLabel="0,00 p.p. (Atual)" />
    <DropdownOption value="0.5" valueLabel="+0,50 p.p." />
    <DropdownOption value="1.0" valueLabel="+1,00 p.p." />
    <DropdownOption value="1.5" valueLabel="+1,50 p.p." />
  </Dropdown>

  <Dropdown name=choque_ipca title="Choque IPCA" defaultValue="0">
    <DropdownOption value="-0.5" valueLabel="-0,50 p.p." />
    <DropdownOption value="0" valueLabel="0,00 p.p. (Consenso)" />
    <DropdownOption value="0.5" valueLabel="+0,50 p.p." />
    <DropdownOption value="1.0" valueLabel="+1,00 p.p." />
  </Dropdown>

  <Dropdown name=choque_fx title="Choque Câmbio" defaultValue="0">
    <DropdownOption value="-5" valueLabel="-5%" />
    <DropdownOption value="0" valueLabel="0% (PTAX Atual)" />
    <DropdownOption value="5" valueLabel="+5%" />
    <DropdownOption value="10" valueLabel="+10%" />
  </Dropdown>
</div>

```sql regime_atual
SELECT
    data,
    selic_meta,
    ipca_focus_ano,
    juro_real_ex_ante,
    regime_monetario
FROM bcb_macro.vw_macro_regime
ORDER BY data DESC
LIMIT 1
```

```sql ptax_risco_atual
SELECT
    r.data_referencia,
    r.cotacao_venda,
    r.vol_anualizada_21d,
    r.zscore_252d,
    f.mediana_base0 AS focus_cambio_2026,
    (r.cotacao_venda / f.mediana_base0 - 1) * 100.0 AS premio_vs_focus_pct
FROM bcb_macro.ptax_risk_metrics r
CROSS JOIN (
    SELECT mediana_base0
    FROM bcb_macro.vw_focus_repricing
    WHERE indicador = 'Câmbio' AND data_referencia = '2026'
    LIMIT 1
) f
WHERE r.moeda = 'USD'
ORDER BY r.data_referencia DESC
LIMIT 1
```

<div class="section-kicker">Radar de Sinais Macroeconômicos</div>

<div class="kpi-grid-5">
  <KPITerminalCard data={regime_atual} value="juro_real_ex_ante" dateCol="data" code="JURO REAL" title="Juro Real Ex-Ante" suffix="%" decimals={2} signed={true} subtitle="Selic vs IPCA Focus" icon="percent" />
  <KPITerminalCard data={regime_atual} value="regime_monetario" dateCol="data" code="REGIME" title="Política Monetária" subtitle="Classificação automática" icon="bank" />
  <KPITerminalCard data={ptax_risco_atual} value="zscore_252d" dateCol="data_referencia" code="FX Z-SCORE" title="Desvio PTAX (252d)" suffix="σ" decimals={2} signed={true} subtitle="Distância da média 12m" icon="alert" />
  <KPITerminalCard data={ptax_risco_atual} value="vol_anualizada_21d" dateCol="data_referencia" code="VOL 21D" title="Volatilidade PTAX" suffix="%" decimals={2} subtitle="Anualizada (ret. log)" icon="activity" />
  <KPITerminalCard data={ptax_risco_atual} value="premio_vs_focus_pct" dateCol="data_referencia" code="FX GAP" title="Prêmio vs Focus 2026" suffix="%" decimals={2} signed={true} subtitle="Spot vs Consenso" icon="dollar" />
</div>

```sql simulador
WITH base AS (
    SELECT
        r.selic_meta,
        r.ipca_focus_ano,
        r.juro_real_ex_ante,
        p.cotacao_venda,
        f.mediana_base0 AS focus_cambio
    FROM (SELECT * FROM bcb_macro.vw_macro_regime ORDER BY data DESC LIMIT 1) r
    CROSS JOIN (SELECT cotacao_venda FROM bcb_macro.ptax_risk_metrics WHERE moeda = 'USD' ORDER BY data_referencia DESC LIMIT 1) p
    CROSS JOIN (SELECT mediana_base0 FROM bcb_macro.vw_focus_repricing WHERE indicador = 'Câmbio' AND data_referencia = '2026' LIMIT 1) f
),
cenarios AS (
    SELECT
        selic_meta + CAST('${inputs.choque_selic.value}' AS DOUBLE) AS selic_sim,
        ipca_focus_ano + CAST('${inputs.choque_ipca.value}' AS DOUBLE) AS ipca_sim,
        cotacao_venda * (1 + CAST('${inputs.choque_fx.value}' AS DOUBLE) / 100.0) AS ptax_sim,
        focus_cambio,
        juro_real_ex_ante AS juro_real_atual
    FROM base
)
SELECT
    selic_sim AS selic_simulada,
    ipca_sim AS ipca_simulado,
    ((1 + selic_sim / 100.0) / (1 + ipca_sim / 100.0) - 1) * 100.0 AS juro_real_simulado,
    (((1 + selic_sim / 100.0) / (1 + ipca_sim / 100.0) - 1) * 100.0) - juro_real_atual AS delta_juro_real_pp,
    ptax_sim AS ptax_simulada,
    (ptax_sim / focus_cambio - 1) * 100.0 AS premio_fx_simulado_pct
FROM cenarios
```

<div class="section-kicker">Simulador Interativo de Cenários (Recalculado em Tempo Real)</div>

<div class="kpi-grid-6">
  <KPITerminalCard data={simulador} value="selic_simulada" code="SIMULAÇÃO" title="Selic Simulada" suffix="%" decimals={2} icon="percent" />
  <KPITerminalCard data={simulador} value="ipca_simulado" code="SIMULAÇÃO" title="IPCA Simulado" suffix="%" decimals={2} icon="trend" />
  <KPITerminalCard data={simulador} value="juro_real_simulado" code="SIMULAÇÃO" title="Juro Real Simulado" suffix="%" decimals={2} signed={true} icon="bank" />
  <KPITerminalCard data={simulador} value="delta_juro_real_pp" code="DELTA" title="Delta Juro Real" suffix=" p.p." decimals={2} signed={true} icon="flow" />
  <KPITerminalCard data={simulador} value="ptax_simulada" code="SIMULAÇÃO" title="PTAX Simulada" prefix="R$ " decimals={4} icon="dollar" />
  <KPITerminalCard data={simulador} value="premio_fx_simulado_pct" code="DELTA" title="Prêmio vs Focus" suffix="%" decimals={2} signed={true} icon="alert" />
</div>

```sql focus_repricing_tabela
SELECT
    indicador,
    data_referencia AS ano,
    mediana_base0 AS base_30d,
    mediana_base1 AS base_5d,
    repricing_b1_vs_b0 AS repricing_5d_vs_30d,
    drift_30d,
    desvio_padrao AS dispersao,
    CASE
        WHEN repricing_b1_vs_b0 > 0.01 THEN 'Revisão Altista'
        WHEN repricing_b1_vs_b0 < -0.01 THEN 'Revisão Baixista'
        ELSE 'Estável'
    END AS sinal
FROM bcb_macro.vw_focus_repricing
WHERE TRY_CAST(data_referencia AS INTEGER) BETWEEN 2026 AND 2028
ORDER BY indicador, ano
```

```sql regime_serie
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.vw_macro_regime
)
SELECT
    r.data,
    r.juro_real_ex_ante,
    r.selic_meta,
    r.ipca_focus_ano
FROM bcb_macro.vw_macro_regime r
CROSS JOIN limite l
WHERE date_diff('day', r.data, l.max_data) <= CAST('${inputs.horizonte_intel.value}' AS INTEGER)
ORDER BY r.data
```

```sql vol_ptax_serie
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data FROM bcb_macro.ptax_risk_metrics WHERE moeda = 'USD'
)
SELECT
    p.data_referencia AS data,
    p.vol_anualizada_21d,
    p.zscore_252d
FROM bcb_macro.ptax_risk_metrics p
CROSS JOIN limite l
WHERE p.moeda = 'USD'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_intel.value}' AS INTEGER)
ORDER BY p.data_referencia
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Repricing Focus — Base 1 (5d úteis) vs Base 0 (30d)</div>
    <div class="terminal-panel-sub">vw_focus_repricing · Drift 30d e dispersão institucional</div>
    <DataTable data={focus_repricing_tabela} rows=12>
      <Column id=indicador title="Indicador" />
      <Column id=ano title="Ano" />
      <Column id=base_30d title="Base 30d" fmt=num2 />
      <Column id=base_5d title="Base 5d" fmt=num2 />
      <Column id=repricing_5d_vs_30d title="Repricing" fmt=num3 />
      <Column id=drift_30d title="Drift 30d" fmt=num3 />
      <Column id=sinal title="Sinal" />
    </DataTable>
  </div>
  <div class="terminal-panel">
    <div class="terminal-panel-title">Juro Real Ex-Ante vs Selic Nominal e IPCA Focus</div>
    <div class="terminal-panel-sub">vw_macro_regime · Juro Real (azul) vs Selic e IPCA (cinza)</div>
    <LineChart
      data={regime_serie}
      x=data
      y={['juro_real_ex_ante', 'selic_meta', 'ipca_focus_ano']}
      yFmt=num2
      yGridlines=false
      xGridlines=false
      colorPalette={['#3b82f6', '#737373', '#525252']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=240
    />
  </div>
</div>

<div class="terminal-panel">
  <div class="terminal-panel-title">Volatilidade anualizada de 21 dias — PTAX USD/BRL</div>
  <div class="terminal-panel-sub">ptax_risk_metrics · desvio-padrão anualizado dos retornos log diários</div>
  <LineChart
    data={vol_ptax_serie}
    x=data
    y=vol_anualizada_21d
    yFmt=num2
    yGridlines=false
    xGridlines=false
    colorPalette={['#3b82f6']}
    echartsOptions={{ backgroundColor: 'transparent' }}
    chartAreaHeight=200
  />
</div>
