---
title: Inteligência de Mercado & Simulador
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Inteligência de Mercado &amp; Simulador de Cenários</h1>
    <p class="page-subtitle">Juro real ex-ante · Repricing Focus (5d vs 30d) · Risco e volatilidade PTAX · Stress test instantâneo</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <ButtonGroup name=horizonte_intel>
        <ButtonGroupItem valueLabel="2 Anos" value="730" />
        <ButtonGroupItem valueLabel="5 Anos" value="1825" default />
        <ButtonGroupItem valueLabel="10 Anos" value="3650" />
      </ButtonGroup>

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

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Simulador ativo</span> · DuckDB-WASM</span>
    </div>
  </div>
</div>

```sql regime_atual
SELECT
    data,
    selic_meta,
    ipca_focus_ano,
    juro_real_ex_ante,
    regime_monetario,
    CASE WHEN regime_monetario = 'Restritivo' THEN 1 ELSE 0 END AS alerta_regime
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
    CASE WHEN ABS(r.zscore_252d) >= 2.0 THEN 1 ELSE 0 END AS alerta_zscore,
    f.mediana_base0 AS focus_cambio_atual,
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
  <KPITerminalCard data={regime_atual} value="juro_real_ex_ante" dateCol="data" code="JURO REAL" title="Juro Real Ex-Ante" suffix="%" decimals={2} signed={true} subtitle="Selic vs Focus" icon="percent" />
  <KPITerminalCard data={regime_atual} value="regime_monetario" dateCol="data" code="REGIME" title="Regime Monetário" subtitle="Regime atual" icon="bank" alertCol="alerta_regime" />
  <KPITerminalCard data={ptax_risco_atual} value="zscore_252d" dateCol="data_referencia" code="FX Z-SCORE" title="Desvio PTAX (252d)" suffix="σ" decimals={2} signed={true} subtitle="Alerta |Z| ≥ 2σ" icon="alert" alertCol="alerta_zscore" />
  <KPITerminalCard data={ptax_risco_atual} value="vol_anualizada_21d" dateCol="data_referencia" code="VOL 21D" title="Volatilidade PTAX" suffix="%" decimals={2} subtitle="Anualizada 21d" icon="activity" />
  <KPITerminalCard data={ptax_risco_atual} value="premio_vs_focus_pct" dateCol="data_referencia" code="FX GAP" title="Prêmio Spot vs Focus" suffix="%" decimals={2} signed={true} subtitle="Spot vs Focus" icon="dollar" />
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
    CROSS JOIN (
        SELECT cotacao_venda
        FROM bcb_macro.ptax_risk_metrics
        WHERE moeda = 'USD'
        ORDER BY data_referencia DESC
        LIMIT 1
    ) p
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
        CAST('${inputs.choque_fx.value}' AS DOUBLE) AS choque_fx_val,
        focus_cambio,
        juro_real_ex_ante AS juro_real_atual
    FROM base
)
SELECT
    selic_sim AS selic_simulada,
    ipca_sim AS ipca_simulado,
    ((1 + selic_sim / 100.0) / (1 + ipca_sim / 100.0) - 1) * 100.0 AS juro_real_simulado,
    (((1 + selic_sim / 100.0) / (1 + ipca_sim / 100.0) - 1) * 100.0) - juro_real_atual AS delta_juro_real_pp,
    CASE WHEN ABS((((1 + selic_sim / 100.0) / (1 + ipca_sim / 100.0) - 1) * 100.0) - juro_real_atual) > 0.001 THEN 1 ELSE 0 END AS alerta_delta_juro,
    ptax_sim AS ptax_simulada,
    (ptax_sim / focus_cambio - 1) * 100.0 AS premio_fx_simulado_pct,
    CASE WHEN ABS(choque_fx_val) > 0.001 THEN 1 ELSE 0 END AS alerta_choque_fx
FROM cenarios
```

<div class="terminal-panel" style="margin-block-end: 18px;">
  <div class="terminal-panel-title">Qual o impacto imediato dos choques escolhidos?</div>
  <div class="terminal-panel-sub">Cenário recalculado em tempo real sobre a última posição de Selic, IPCA Focus e PTAX</div>
  <div class="kpi-grid-6" style="margin-block-end: 0;">
    <KPITerminalCard data={simulador} value="selic_simulada" code="SIMULAÇÃO" title="Selic Simulada" suffix="%" decimals={2} subtitle="Taxa nominal" icon="percent" />
    <KPITerminalCard data={simulador} value="ipca_simulado" code="SIMULAÇÃO" title="IPCA Simulado" suffix="%" decimals={2} subtitle="Expectativa 12m" icon="trend" />
    <KPITerminalCard data={simulador} value="juro_real_simulado" code="SIMULAÇÃO" title="Juro Real Simulado" suffix="%" decimals={2} signed={true} subtitle="Equação de Fisher" icon="bank" />
    <KPITerminalCard data={simulador} value="delta_juro_real_pp" code="DELTA" title="Delta Juro Real" suffix=" p.p." decimals={2} signed={true} subtitle="Frente ao atual" icon="flow" alertCol="alerta_delta_juro" />
    <KPITerminalCard data={simulador} value="ptax_simulada" code="SIMULAÇÃO" title="PTAX Simulada" prefix="R$ " decimals={4} subtitle="USD/BRL" icon="dollar" />
    <KPITerminalCard data={simulador} value="premio_fx_simulado_pct" code="DELTA" title="Prêmio vs Focus" suffix="%" decimals={2} signed={true} subtitle="Gap simulado" icon="alert" alertCol="alerta_choque_fx" />
  </div>
</div>

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

```sql focus_repricing_tabela
WITH ano_atual AS (
    SELECT YEAR(MAX(data_base0)) AS ano FROM bcb_macro.vw_focus_repricing
)
SELECT
    f.indicador,
    f.data_referencia AS ano,
    f.mediana_base0 AS base_30d,
    f.mediana_base1 AS base_5d,
    f.repricing_b1_vs_b0 AS repricing_5d_vs_30d,
    f.drift_30d,
    CASE
        WHEN f.repricing_b1_vs_b0 > 0.01 THEN 'Revisão Altista'
        WHEN f.repricing_b1_vs_b0 < -0.01 THEN 'Revisão Baixista'
        ELSE 'Estável'
    END AS sinal,
    CASE
        WHEN f.repricing_b1_vs_b0 > 0.01 THEN 'alert'
        WHEN f.repricing_b1_vs_b0 < -0.01 THEN 'neutral'
        ELSE 'muted'
    END AS sinal_tone
FROM bcb_macro.vw_focus_repricing f
CROSS JOIN ano_atual a
WHERE TRY_CAST(f.data_referencia AS INTEGER) BETWEEN a.ano AND a.ano + 2
ORDER BY f.indicador, ano
```

<div class="terminal-grid-chart-table">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como o Juro Real Ex-Ante se desloca frente à Selic e ao IPCA?</div>
    <div class="terminal-panel-sub">Juro real ex-ante (laranja) em comparação à Selic nominal e IPCA Focus (cinza) · % a.a.</div>
    <TerminalLineChart
      data={regime_serie}
      x="data"
      y={['juro_real_ex_ante', 'selic_meta', 'ipca_focus_ano']}
      labels={['Juro Real Ex-Ante', 'Selic Meta', 'IPCA Focus']}
      colors={['#ff6b00', '#737373', '#525252']}
      suffix="%"
      decimals={2}
      height="380px"
    />
  </div>

  <ConditionalTable
    data={focus_repricing_tabela}
    title="Onde o mercado revisou projeções nos últimos 5 dias úteis?"
    subtitle="Focus Base 1 (5d) vs Base 0 (30d) · Revisão Altista em destaque laranja"
    minWidth="560px"
    columns={[
      { key: 'indicador', label: 'Indicador', format: 'text', emphasis: 'primary' },
      { key: 'ano', label: 'Ano', format: 'id', emphasis: 'muted' },
      { key: 'base_30d', label: '30d', align: 'right', format: 'focusVal', emphasis: 'muted' },
      { key: 'base_5d', label: '5d', align: 'right', format: 'focusVal', emphasis: 'primary' },
      { key: 'repricing_5d_vs_30d', label: 'Repricing', align: 'right', format: 'focusDelta' },
      { key: 'drift_30d', label: 'Drift 30d', align: 'right', format: 'focusDelta', emphasis: 'muted' },
      { key: 'sinal', label: 'Sinal', align: 'right', format: 'text', toneCol: 'sinal_tone' }
    ]}
  />
</div>

```sql vol_ptax_serie
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data
    FROM bcb_macro.ptax_risk_metrics
    WHERE moeda = 'USD'
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

<div class="terminal-panel">
  <div class="terminal-panel-title">Como evoluiu a volatilidade anualizada (21d) da PTAX USD/BRL?</div>
  <div class="terminal-panel-sub">Desvio-padrão anualizado dos retornos logarítmicos diários · janela móvel de 21 pregões</div>
  <TerminalLineChart
    data={vol_ptax_serie}
    x="data"
    y="vol_anualizada_21d"
    labels={['Volatilidade 21d']}
    suffix="%"
    decimals={2}
    height="240px"
  />
</div>
