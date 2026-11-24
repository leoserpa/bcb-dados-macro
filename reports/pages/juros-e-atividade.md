---
title: Juros, Atividade Econômica, Crédito & Fiscal (SGS)
---

Séries domésticas do **Sistema Gerenciador de Séries Temporais (SGS)** do Banco Central (`432`, `11`, `24364`, `13762`, `20631`, `21082`) — histórico completo 2010–2026.

<div class="filter-bar">
  <Dropdown name=horizonte title="Horizonte Temporal" defaultValue="1825">
    <DropdownOption value="730" valueLabel="Últimos 2 anos" />
    <DropdownOption value="1825" valueLabel="Últimos 5 anos" />
    <DropdownOption value="3650" valueLabel="Últimos 10 anos" />
    <DropdownOption value="36500" valueLabel="Todo o histórico (2010+)" />
  </Dropdown>
</div>

```sql sgs_domesticos_kpi
SELECT
    MAX(CASE WHEN indicador_id = '432' THEN valor END) AS meta_selic,
    MAX(CASE WHEN indicador_id = '432' THEN data_observacao END) AS d432,
    MAX(CASE WHEN indicador_id = '11' THEN valor END) AS selic_diaria,
    MAX(CASE WHEN indicador_id = '11' THEN data_observacao END) AS d11,
    MAX(CASE WHEN indicador_id = '24364' THEN valor END) AS ibc_br,
    MAX(CASE WHEN indicador_id = '24364' THEN data_observacao END) AS d24364,
    MAX(CASE WHEN indicador_id = '13762' THEN valor END) AS dbgg_pib,
    MAX(CASE WHEN indicador_id = '13762' THEN data_observacao END) AS d13762,
    MAX(CASE WHEN indicador_id = '20631' THEN valor END) AS concessoes,
    MAX(CASE WHEN indicador_id = '20631' THEN data_observacao END) AS d20631,
    MAX(CASE WHEN indicador_id = '21082' THEN valor END) AS inadimplencia,
    MAX(CASE WHEN indicador_id = '21082' THEN data_observacao END) AS d21082
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={sgs_domesticos_kpi} value="meta_selic" dateCol="d432" code="SGS 432" title="Meta Selic Copom" suffix="%" decimals={2} subtitle="Evento · % a.a." icon="percent" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="selic_diaria" dateCol="d11" code="SGS 11" title="Taxa Selic Diária" suffix="%" decimals={4} subtitle="Diária · % a.d." icon="trend" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="ibc_br" dateCol="d24364" code="SGS 24364" title="IBC-Br Dessaz." decimals={2} subtitle="Mensal · Índice" icon="activity" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="dbgg_pib" dateCol="d13762" code="SGS 13762" title="DBGG / PIB" suffix="%" decimals={2} subtitle="Mensal · % PIB" icon="bank" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="concessoes" dateCol="d20631" code="SGS 20631" title="Concessões Crédito" prefix="R$ " decimals={0} subtitle="Mensal · R$ mi" icon="dollar" />
  <KPITerminalCard data={sgs_domesticos_kpi} value="inadimplencia" dateCol="d21082" code="SGS 21082" title="Inadimplência SFN" suffix="%" decimals={2} subtitle="Mensal · % cart." icon="alert" />
</div>

```sql selic_meta
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 432
)
SELECT s.data, s.valor AS meta_selic
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 432
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte.value}' AS INTEGER)
ORDER BY s.data
```

```sql selic_diaria
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 11
)
SELECT s.data, s.valor AS selic_diaria
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 11
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte.value}' AS INTEGER)
ORDER BY s.data
```

<Grid cols=2>
    <LineChart
        data={selic_meta}
        x=data
        y=meta_selic
        title="Trajetória da Meta Selic definida pelo Copom"
        subtitle="SGS 432 · Copom (% a.a.)"
        yFmt=num2
        step=true
        yGridlines=false
        xGridlines=false
        colorPalette={['#3b82f6']}
    />
    <LineChart
        data={selic_diaria}
        x=data
        y=selic_diaria
        title="Taxa Selic efetiva diária"
        subtitle="SGS 11 · Taxa efetiva diária (%)"
        yFmt=num4
        yGridlines=false
        xGridlines=false
        colorPalette={['#737373']}
    />
</Grid>

```sql ibc_br
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 24364
)
SELECT s.data, s.valor AS ibc_br
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 24364
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte.value}' AS INTEGER)
ORDER BY s.data
```

```sql dbgg_pib
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 13762
)
SELECT s.data, s.valor AS dbgg_pib
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 13762
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte.value}' AS INTEGER)
ORDER BY s.data
```

<Grid cols=2>
    <LineChart
        data={ibc_br}
        x=data
        y=ibc_br
        title="Atividade econômica — IBC-Br com ajuste sazonal"
        subtitle="SGS 24364 · Índice com ajuste sazonal"
        yFmt=num2
        yGridlines=false
        xGridlines=false
        colorPalette={['#737373']}
    />
    <LineChart
        data={dbgg_pib}
        x=data
        y=dbgg_pib
        title="Trajetória fiscal — Dívida Bruta do Governo Geral (% PIB)"
        subtitle="SGS 13762 · Dívida Bruta do Governo Geral (% PIB)"
        yFmt=num2
        yGridlines=false
        xGridlines=false
        colorPalette={['#3b82f6']}
    />
</Grid>

```sql concessoes_credito
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 20631
)
SELECT s.data, s.valor AS concessoes_r_mi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 20631
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte.value}' AS INTEGER)
ORDER BY s.data
```

```sql inadimplencia_sfn
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 21082
)
SELECT s.data, s.valor AS inadimplencia_pct
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 21082
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte.value}' AS INTEGER)
ORDER BY s.data
```

<Grid cols=2>
    <BarChart
        data={concessoes_credito}
        x=data
        y=concessoes_r_mi
        title="Volume mensal de concessões totais de crédito"
        subtitle="SGS 20631 · R$ milhões"
        yFmt=num0
        yGridlines=false
        xGridlines=false
        colorPalette={['#525252']}
    />
    <LineChart
        data={inadimplencia_sfn}
        x=data
        y=inadimplencia_pct
        title="Evolução da inadimplência total do SFN"
        subtitle="SGS 21082 · % da carteira total"
        yFmt=num2
        yGridlines=false
        xGridlines=false
        colorPalette={['#3b82f6']}
    />
</Grid>
