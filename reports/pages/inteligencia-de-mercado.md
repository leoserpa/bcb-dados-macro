---
title: Inteligência, Regimes & Simulador
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Inteligência, Regimes & Simulador</h1>
    <p class="page-subtitle">Juro real ex-ante, repricing do Boletim Focus (5d vs 30d), risco cambial e cenários em tempo real</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=horizonte_intel>
        <ButtonGroupItem valueLabel="2 Anos" value="730" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
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
  </div>
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
    f.mediana_base0 AS focus_cambio_ano,
    (r.cotacao_venda / f.mediana_base0 - 1) * 100.0 AS premio_vs_focus_pct
FROM bcb_macro.ptax_risk_metrics r
CROSS JOIN (
    SELECT mediana_base0
    FROM bcb_macro.vw_focus_repricing
    WHERE indicador = 'Câmbio'
      AND TRY_CAST(data_referencia AS INTEGER) = (
          SELECT YEAR(MAX(data_base0)) FROM bcb_macro.vw_focus_repricing
      )
    LIMIT 1
) f
WHERE r.moeda = 'USD'
ORDER BY r.data_referencia DESC
LIMIT 1
```

<div class="kpi-grid-5">
  <KPITerminalCard data={regime_atual} value="juro_real_ex_ante" dateCol="data" title="Juro Real Ex-Ante" suffix="%" decimals={2} signed={true} subtitle="Selic vs IPCA Focus" accent={true} />
  <KPITerminalCard data={regime_atual} value="regime_monetario" dateCol="data" title="Política Monetária" subtitle="Classificação de regime" accent={true} />
  <KPITerminalCard data={ptax_risco_atual} value="zscore_252d" dateCol="data_referencia" title="Desvio PTAX (252d)" suffix="σ" decimals={2} signed={true} subtitle="Distância da média 12m" accent={true} />
  <KPITerminalCard data={ptax_risco_atual} value="vol_anualizada_21d" dateCol="data_referencia" title="Volatilidade PTAX 21d" suffix="%" decimals={2} subtitle="Retornos log anualizados" />
  <KPITerminalCard data={ptax_risco_atual} value="premio_vs_focus_pct" dateCol="data_referencia" title="Prêmio vs Focus" suffix="%" decimals={2} signed={true} subtitle="Spot frente ao consenso" />
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
    CROSS JOIN (
        SELECT mediana_base0
        FROM bcb_macro.vw_focus_repricing
        WHERE indicador = 'Câmbio'
          AND TRY_CAST(data_referencia AS INTEGER) = (
              SELECT YEAR(MAX(data_base0)) FROM bcb_macro.vw_focus_repricing
          )
        LIMIT 1
    ) f
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

```sql focus_repricing_tabela
WITH ano_atual AS (
    SELECT YEAR(MAX(data_base0)) AS ano_ref FROM bcb_macro.vw_focus_repricing
)
SELECT
    r.indicador,
    r.data_referencia AS ano,
    r.mediana_base0 AS base_30d,
    r.mediana_base1 AS base_5d,
    r.repricing_b1_vs_b0 AS repricing_5d_vs_30d,
    r.drift_30d,
    CASE
        WHEN r.repricing_b1_vs_b0 > 0.01 THEN 'Altista'
        WHEN r.repricing_b1_vs_b0 < -0.01 THEN 'Baixista'
        ELSE 'Estável'
    END AS sinal
FROM bcb_macro.vw_focus_repricing r
CROSS JOIN ano_atual a
WHERE TRY_CAST(r.data_referencia AS INTEGER) BETWEEN a.ano_ref AND a.ano_ref + 2
ORDER BY r.indicador, ano
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
WHERE date_diff('day', r.data, l.max_data) <= CAST('${inputs.horizonte_intel}' AS INTEGER)
ORDER BY r.data
```

```sql vol_ptax_serie
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data FROM bcb_macro.ptax_risk_metrics WHERE moeda = 'USD'
)
SELECT
    p.data_referencia AS data,
    p.vol_anualizada_21d
FROM bcb_macro.ptax_risk_metrics p
CROSS JOIN limite l
WHERE p.moeda = 'USD'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_intel}' AS INTEGER)
ORDER BY p.data_referencia
```

<div class="terminal-grid-asym">
  <div class="terminal-stack">
    <div class="terminal-panel">
      <div class="panel-head">
        <div>
          <div class="terminal-panel-title">Simulador Interativo de Cenários</div>
          <div class="terminal-panel-sub">Recalculado instantaneamente a partir dos choques selecionados acima</div>
        </div>
      </div>
      <div class="kpi-grid-4" style="margin-block-end: 0;">
        <KPITerminalCard data={simulador} value="selic_simulada" title="Selic Simulada" suffix="%" decimals={2} subtitle="Nominal Copom" />
        <KPITerminalCard data={simulador} value="ipca_simulado" title="IPCA Simulado" suffix="%" decimals={2} subtitle="Expectativa Focus" />
        <KPITerminalCard data={simulador} value="juro_real_simulado" title="Juro Real Sim." suffix="%" decimals={2} signed={true} subtitle="Equação de Fisher" accent={true} />
        <KPITerminalCard data={simulador} value="ptax_simulada" title="PTAX Simulada" prefix="R$ " decimals={4} subtitle="USD/BRL projetada" accent={true} />
      </div>
    </div>

    <div class="terminal-panel">
      <div class="terminal-panel-title">Juro Real Ex-Ante vs Selic Nominal e IPCA Focus</div>
      <div class="terminal-panel-sub">Juro real ex-ante em destaque (azul) frente à Selic nominal e inflação esperada (cinza)</div>
      <LineChart
        data={regime_serie}
        x=data
        y={['juro_real_ex_ante', 'selic_meta', 'ipca_focus_ano']}
        yFmt=num2
        yGridlines=false
        xGridlines=false
        colorPalette={['#3b82f6', '#737373', '#525252']}
        echartsOptions={{ backgroundColor: 'transparent' }}
        chartAreaHeight=225
      />
    </div>
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Repricing Focus — 5d vs 30d</div>
    <div class="terminal-panel-sub">Revisões recentes nas medianas de mercado (Base 1 menos Base 0)</div>
    <DataTable data={focus_repricing_tabela} rows=12>
      <Column id=indicador title="Indicador" />
      <Column id=ano title="Ano" />
      <Column id=base_30d title="30d" fmt=num2 />
      <Column id=base_5d title="5d" fmt=num2 />
      <Column id=repricing_5d_vs_30d title="Repricing" fmt=num3 />
      <Column id=sinal title="Sinal" />
    </DataTable>
  </div>
</div>

<div class="terminal-panel">
  <div class="terminal-panel-title">Volatilidade Anualizada de 21 Dias — PTAX USD/BRL</div>
  <div class="terminal-panel-sub">Desvio-padrão anualizado dos retornos logarítmicos diários (%)</div>
  <LineChart
    data={vol_ptax_serie}
    x=data
    y=vol_anualizada_21d
    yFmt=num2
    yGridlines=false
    xGridlines=false
    colorPalette={['#3b82f6']}
    echartsOptions={{ backgroundColor: 'transparent' }}
    chartAreaHeight=190
  />
</div>
