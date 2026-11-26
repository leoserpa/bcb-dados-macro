---
title: Expectativas de Mercado — Boletim Focus
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Expectativas de Mercado — Boletim Focus</h1>
    <p class="page-subtitle">IPCA, Selic, Câmbio e PIB Total · Base 0 (30 dias), Base 1 (5 dias úteis) e Top 5 de médio prazo</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <Dropdown data={focus_indicadores} name=indicador value=indicador title="Indicador" defaultValue="IPCA" />
      <Dropdown data={focus_anos} name=ano_ref value=data_referencia title="Ano Ref." defaultValue="2026" />
      <ButtonGroup name=base_calculo>
        <ButtonGroupItem valueLabel="Base 0 · 30d" value="0" default />
        <ButtonGroupItem valueLabel="Base 1 · 5d" value="1" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip">Série selecionada · <span class="status-chip-accent">{inputs.indicador.value} ({inputs.ano_ref.value})</span></span>
    </div>
  </div>
</div>

```sql focus_indicadores
SELECT DISTINCT indicador
FROM bcb_macro.focus_expectations
ORDER BY indicador
```

```sql focus_anos
SELECT DISTINCT data_referencia
FROM bcb_macro.focus_expectations
WHERE TRY_CAST(data_referencia AS INTEGER) >= 2020
ORDER BY data_referencia DESC
```

```sql focus_kpi
SELECT
    data,
    mediana,
    media,
    minimo,
    maximo,
    desvio_padrao,
    numero_respondentes
FROM bcb_macro.focus_expectations
WHERE indicador = '${inputs.indicador.value}'
  AND data_referencia = '${inputs.ano_ref.value}'
  AND base_calculo = CAST('${inputs.base_calculo}' AS INTEGER)
ORDER BY data DESC
LIMIT 1
```

<div class="kpi-grid-6">
  <KPITerminalCard data={focus_kpi} value="mediana" dateCol="data" code="MEDIANA" title="Mediana Focus" prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''} suffix={inputs.indicador.value === 'Câmbio' ? '' : '%'} decimals={2} subtitle="Consenso" icon="trend" />
  <KPITerminalCard data={focus_kpi} value="media" dateCol="data" code="MÉDIA" title="Média Focus" prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''} suffix={inputs.indicador.value === 'Câmbio' ? '' : '%'} decimals={2} subtitle="Média" icon="activity" />
  <KPITerminalCard data={focus_kpi} value="minimo" dateCol="data" code="MÍNIMO" title="Piso das Projeções" prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''} suffix={inputs.indicador.value === 'Câmbio' ? '' : '%'} decimals={2} subtitle="Mínimo" icon="flow" />
  <KPITerminalCard data={focus_kpi} value="maximo" dateCol="data" code="MÁXIMO" title="Teto das Projeções" prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''} suffix={inputs.indicador.value === 'Câmbio' ? '' : '%'} decimals={2} subtitle="Máximo" icon="alert" />
  <KPITerminalCard data={focus_kpi} value="desvio_padrao" dateCol="data" code="DESVIO" title="Desvio-Padrão" prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''} suffix={inputs.indicador.value === 'Câmbio' ? '' : ' p.p.'} decimals={2} subtitle="Dispersão" icon="percent" />
  <KPITerminalCard data={focus_kpi} value="numero_respondentes" dateCol="data" code="AMOSTRA" title="Respondentes" decimals={0} subtitle="Instituições" icon="users" />
</div>

```sql focus_serie
SELECT
    data,
    mediana,
    media,
    minimo,
    maximo
FROM bcb_macro.focus_expectations
WHERE indicador = '${inputs.indicador.value}'
  AND data_referencia = '${inputs.ano_ref.value}'
  AND base_calculo = CAST('${inputs.base_calculo}' AS INTEGER)
ORDER BY data
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como evoluiu a mediana frente à média — {inputs.indicador.value} ({inputs.ano_ref.value})?</div>
    <div class="terminal-panel-sub">Mediana em destaque (laranja) vs média institucional (cinza)</div>
    <TerminalLineChart
      data={focus_serie}
      x="data"
      y={['mediana', 'media']}
      labels={['Mediana', 'Média']}
      colors={['#ff6b00', '#737373']}
      prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''}
      suffix={inputs.indicador.value === 'Câmbio' ? '' : '%'}
      decimals={2}
      height="245px"
    />
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual a amplitude entre piso e teto das projeções?</div>
    <div class="terminal-panel-sub">Mediana (laranja) delimitada pelos extremos mínimo e máximo (cinza)</div>
    <TerminalLineChart
      data={focus_serie}
      x="data"
      y={['mediana', 'minimo', 'maximo']}
      labels={['Mediana', 'Mínimo', 'Máximo']}
      colors={['#ff6b00', '#525252', '#525252']}
      dashedIndices={[1, 2]}
      prefix={inputs.indicador.value === 'Câmbio' ? 'R$ ' : ''}
      suffix={inputs.indicador.value === 'Câmbio' ? '' : '%'}
      decimals={2}
      height="245px"
    />
  </div>
</div>

```sql focus_curva
WITH ultima_coleta AS (
    SELECT
        indicador,
        data_referencia,
        MAX(data) AS max_data
    FROM bcb_macro.focus_expectations
    WHERE base_calculo = CAST('${inputs.base_calculo}' AS INTEGER)
    GROUP BY 1, 2
),
ano_atual AS (
    SELECT YEAR(MAX(data)) AS ano FROM bcb_macro.focus_expectations
)
SELECT
    f.indicador,
    f.data_referencia AS ano_referencia,
    f.data AS data_coleta,
    f.mediana,
    f.media,
    f.minimo,
    f.maximo,
    f.numero_respondentes AS respondentes
FROM bcb_macro.focus_expectations f
INNER JOIN ultima_coleta u
    ON f.indicador = u.indicador
   AND f.data_referencia = u.data_referencia
   AND f.data = u.max_data
CROSS JOIN ano_atual a
WHERE f.base_calculo = CAST('${inputs.base_calculo}' AS INTEGER)
  AND TRY_CAST(f.data_referencia AS INTEGER) BETWEEN a.ano AND a.ano + 4
ORDER BY f.indicador, f.data_referencia
```

```sql focus_top5_comparativo
WITH ano_atual AS (
    SELECT YEAR(MAX(data_top5)) AS ano FROM bcb_macro.vw_focus_top5_vs_geral
)
SELECT
    t.indicador,
    t.data_referencia AS ano,
    t.data_top5 AS coleta,
    t.mediana_top5,
    t.mediana_geral,
    t.spread_top5_vs_geral AS spread_top5_geral,
    CASE
        WHEN (t.indicador = 'Câmbio' AND ROUND(ABS(t.spread_top5_vs_geral), 3) >= 0.05)
          OR (t.indicador <> 'Câmbio' AND ROUND(ABS(t.spread_top5_vs_geral), 3) >= 0.10)
        THEN 1
        ELSE 0
    END AS alerta_spread,
    t.desvio_top5
FROM bcb_macro.vw_focus_top5_vs_geral t
CROSS JOIN ano_atual a
WHERE t.tipo_calculo = 'M'
  AND TRY_CAST(t.data_referencia AS INTEGER) BETWEEN a.ano AND a.ano + 3
ORDER BY t.indicador, t.data_referencia
```

<ConditionalTable
  data={focus_curva}
  marginBottom={true}
  title="Curva Completa de Expectativas (Base {inputs.base_calculo})"
  subtitle="Última coleta por indicador e ano de referência nos próximos 5 exercícios"
  minWidth="680px"
  columns={[
    { key: 'indicador', label: 'Indicador', format: 'text', emphasis: 'primary' },
    { key: 'ano_referencia', label: 'Ano', format: 'id', emphasis: 'muted' },
    { key: 'data_coleta', label: 'Coleta', format: 'date', emphasis: 'muted' },
    { key: 'mediana', label: 'Mediana', align: 'right', format: 'focusVal', emphasis: 'primary' },
    { key: 'media', label: 'Média', align: 'right', format: 'focusVal', emphasis: 'muted' },
    { key: 'minimo', label: 'Mín.', align: 'right', format: 'focusVal', emphasis: 'muted' },
    { key: 'maximo', label: 'Máx.', align: 'right', format: 'focusVal', emphasis: 'muted' },
    { key: 'respondentes', label: 'Resp.', align: 'right', format: 'num0', emphasis: 'muted' }
  ]}
/>

<ConditionalTable
  data={focus_top5_comparativo}
  title="Focus Top 5 (Médio Prazo) vs Consenso Geral"
  subtitle="Spread em laranja quando Top 5 diverge do consenso (≥ 0,10 pp em IPCA/Selic/PIB ou ≥ R$ 0,05 em Câmbio)"
  minWidth="640px"
  columns={[
    { key: 'indicador', label: 'Indicador', format: 'text', emphasis: 'primary' },
    { key: 'ano', label: 'Ano', format: 'id', emphasis: 'muted' },
    { key: 'coleta', label: 'Coleta', format: 'date', emphasis: 'muted' },
    { key: 'mediana_top5', label: 'Top 5', align: 'right', format: 'focusVal', emphasis: 'primary' },
    { key: 'mediana_geral', label: 'Geral', align: 'right', format: 'focusVal', emphasis: 'muted' },
    { key: 'spread_top5_geral', label: 'Spread', align: 'right', format: 'focusDelta', emphasis: 'muted', alertCol: 'alerta_spread' },
    { key: 'desvio_top5', label: 'Desvio', align: 'right', format: 'focusDesvio', emphasis: 'muted' }
  ]}
/>
