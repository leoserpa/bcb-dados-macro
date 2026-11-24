---
title: Expectativas de Mercado — Boletim Focus (OData)
---

Expectativas anuais coletadas via **API Olinda (Focus)** — 122.217 observações para **IPCA**, **Selic**, **Câmbio** e **PIB Total** (Base 0 e Base 1).

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

<div class="filter-bar">
  <Dropdown data={focus_indicadores} name=indicador value=indicador title="Indicador" defaultValue="IPCA" />
  <Dropdown data={focus_anos} name=ano_ref value=data_referencia title="Ano de Referência" defaultValue="2026" />
  <Dropdown name=base_calculo title="Base de Cálculo" defaultValue="0">
    <DropdownOption value="0" valueLabel="Base 0 — Últimos 30 dias" />
    <DropdownOption value="1" valueLabel="Base 1 — Últimos 5 dias úteis" />
  </Dropdown>
</div>

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
  AND base_calculo = CAST('${inputs.base_calculo.value}' AS INTEGER)
ORDER BY data DESC
LIMIT 1
```

<div class="section-kicker">Última Coleta — {inputs.indicador.value} ({inputs.ano_ref.value})</div>

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
  AND base_calculo = CAST('${inputs.base_calculo.value}' AS INTEGER)
ORDER BY data
```

<Grid cols=2>
    <LineChart
        data={focus_serie}
        x=data
        y={['mediana', 'media']}
        title="Evolução da mediana vs média — {inputs.indicador.value} ({inputs.ano_ref.value})"
        subtitle="Mediana em destaque (azul) vs Média (cinza)"
        yFmt=num2
        yGridlines=false
        xGridlines=false
        colorPalette={['#3b82f6', '#737373']}
        chartAreaHeight=220
    />
    <LineChart
        data={focus_serie}
        x=data
        y={['mediana', 'minimo', 'maximo']}
        title="Dispersão de mercado — Mediana entre piso e teto das projeções"
        subtitle="Mediana (azul) com limites mínimo e máximo (cinza)"
        yFmt=num2
        yGridlines=false
        xGridlines=false
        colorPalette={['#3b82f6', '#525252', '#525252']}
        chartAreaHeight=220
    />
</Grid>

```sql focus_curva
WITH ultima_coleta AS (
    SELECT
        indicador,
        data_referencia,
        MAX(data) AS max_data
    FROM bcb_macro.focus_expectations
    WHERE base_calculo = CAST('${inputs.base_calculo.value}' AS INTEGER)
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
WHERE f.base_calculo = CAST('${inputs.base_calculo.value}' AS INTEGER)
  AND TRY_CAST(f.data_referencia AS INTEGER) BETWEEN a.ano AND a.ano + 4
ORDER BY f.indicador, f.data_referencia
```

### Curva Completa de Expectativas — Todos os Indicadores (2026–2030)

<DataTable data={focus_curva} rows=20>
    <Column id=indicador title="Indicador" />
    <Column id=ano_referencia title="Ano Ref." />
    <Column id=data_coleta title="Data Coleta" />
    <Column id=mediana title="Mediana" fmt=num2 />
    <Column id=media title="Média" fmt=num2 />
    <Column id=minimo title="Mínimo" fmt=num2 />
    <Column id=maximo title="Máximo" fmt=num2 />
    <Column id=respondentes title="Respondentes" fmt=num0 />
</DataTable>
