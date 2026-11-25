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
  <KPITerminalCard data={focus_kpi} value="mediana" dateCol="data" code="MEDIANA" title="Mediana Focus" decimals={2} subtitle="Consenso central" icon="trend" />
  <KPITerminalCard data={focus_kpi} value="media" dateCol="data" code="MÉDIA" title="Média Focus" decimals={2} subtitle="Média institucional" icon="activity" />
  <KPITerminalCard data={focus_kpi} value="minimo" dateCol="data" code="MÍNIMO" title="Piso das Projeções" decimals={2} subtitle="Cenário mais baixo" icon="flow" />
  <KPITerminalCard data={focus_kpi} value="maximo" dateCol="data" code="MÁXIMO" title="Teto das Projeções" decimals={2} subtitle="Cenário mais alto" icon="alert" />
  <KPITerminalCard data={focus_kpi} value="desvio_padrao" dateCol="data" code="DESVIO" title="Desvio-Padrão" decimals={2} subtitle="Dispersão entre casas" icon="percent" />
  <KPITerminalCard data={focus_kpi} value="numero_respondentes" dateCol="data" code="AMOSTRA" title="Respondentes" decimals={0} subtitle="Instituições ativas" icon="users" />
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
    <LineChart
      data={focus_serie}
      x=data
      y={['mediana', 'media']}
      yFmt=num2
      yGridlines=false
      xGridlines=false
      colorPalette={['#ff6b00', '#737373']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=220
    />
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual a amplitude entre piso e teto das projeções?</div>
    <div class="terminal-panel-sub">Mediana (laranja) delimitada pelos extremos mínimo e máximo (cinza)</div>
    <LineChart
      data={focus_serie}
      x=data
      y={['mediana', 'minimo', 'maximo']}
      yFmt=num2
      yGridlines=false
      xGridlines=false
      colorPalette={['#ff6b00', '#525252', '#525252']}
      echartsOptions={{ backgroundColor: 'transparent' }}
      chartAreaHeight=220
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
    t.desvio_top5
FROM bcb_macro.vw_focus_top5_vs_geral t
CROSS JOIN ano_atual a
WHERE t.tipo_calculo = 'M'
  AND TRY_CAST(t.data_referencia AS INTEGER) BETWEEN a.ano AND a.ano + 3
ORDER BY t.indicador, t.data_referencia
```

<div class="terminal-panel" style="margin-block-end: 18px;">
  <div class="terminal-panel-title">Curva Completa de Expectativas (Base {inputs.base_calculo})</div>
  <div class="terminal-panel-sub">Última coleta por indicador e ano de referência nos próximos 5 exercícios</div>
  <DataTable data={focus_curva} rows=16>
    <Column id=indicador title="Indicador" />
    <Column id=ano_referencia title="Ano" />
    <Column id=data_coleta title="Coleta" />
    <Column id=mediana title="Mediana" fmt=num2 />
    <Column id=media title="Média" fmt=num2 />
    <Column id=minimo title="Mín." fmt=num2 />
    <Column id=maximo title="Máx." fmt=num2 />
    <Column id=respondentes title="Resp." fmt=num0 />
  </DataTable>
</div>

<div class="terminal-panel">
  <div class="terminal-panel-title">Focus Top 5 (Médio Prazo) vs Consenso Geral</div>
  <div class="terminal-panel-sub">Diferença entre as 5 instituições mais assertivas e a mediana geral de mercado</div>
  <DataTable data={focus_top5_comparativo} rows=16>
    <Column id=indicador title="Indicador" />
    <Column id=ano title="Ano" />
    <Column id=coleta title="Coleta" />
    <Column id=mediana_top5 title="Top 5" fmt=num2 />
    <Column id=mediana_geral title="Geral" fmt=num2 />
    <Column id=spread_top5_geral title="Spread" fmt=num3 />
    <Column id=desvio_top5 title="Desvio" fmt=num2 />
  </DataTable>
</div>
