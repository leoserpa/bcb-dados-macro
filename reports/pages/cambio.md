---
title: Câmbio (PTAX) & Setor Externo
---

Cotações diárias **PTAX** (priorizando o boletim de fechamento), **Reservas Internacionais (`13982`)** e **Fluxos Cambiais (`13967` e `13970`)**.

<div class="filter-bar">
  <Dropdown name=horizonte_cambio title="Horizonte Temporal" defaultValue="1825">
    <DropdownOption value="365" valueLabel="Último ano" />
    <DropdownOption value="1825" valueLabel="Últimos 5 anos" />
    <DropdownOption value="3650" valueLabel="Últimos 10 anos" />
    <DropdownOption value="36500" valueLabel="Todo o histórico (2010+)" />
  </Dropdown>
</div>

```sql ptax_ultima
SELECT
    data_referencia,
    cotacao_compra,
    cotacao_venda,
    cotacao_venda - cotacao_compra AS spread,
    tipo_boletim
FROM bcb_macro.ptax_daily
WHERE moeda = 'USD'
ORDER BY data_referencia DESC
LIMIT 1
```

```sql externo_sgs
SELECT
    MAX(CASE WHEN indicador_id = '13982' THEN valor END) AS reservas_usd_mi,
    MAX(CASE WHEN indicador_id = '13982' THEN data_observacao END) AS d13982,
    MAX(CASE WHEN indicador_id = '13967' THEN valor END) AS fluxo_com,
    MAX(CASE WHEN indicador_id = '13967' THEN data_observacao END) AS d13967,
    MAX(CASE WHEN indicador_id = '13970' THEN valor END) AS fluxo_fin,
    MAX(CASE WHEN indicador_id = '13970' THEN data_observacao END) AS d13970
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

<div class="kpi-grid-6">
  <KPITerminalCard data={ptax_ultima} value="cotacao_compra" dateCol="data_referencia" code="PTAX COMPRA" title="Cotação Compra" prefix="R$ " decimals={4} subtitle="Boletim Fechamento" icon="dollar" />
  <KPITerminalCard data={ptax_ultima} value="cotacao_venda" dateCol="data_referencia" code="PTAX VENDA" title="Cotação Venda" prefix="R$ " decimals={4} subtitle="Boletim Fechamento" icon="dollar" />
  <KPITerminalCard data={ptax_ultima} value="spread" dateCol="data_referencia" code="SPREAD" title="Spread Compra/Venda" prefix="R$ " decimals={4} subtitle="Paridade USD 1,00" icon="flow" />
  <KPITerminalCard data={externo_sgs} value="reservas_usd_mi" dateCol="d13982" code="SGS 13982" title="Reservas Internac." prefix="$ " decimals={0} subtitle="US$ milhões · Diária" icon="globe" />
  <KPITerminalCard data={externo_sgs} value="fluxo_com" dateCol="d13967" code="SGS 13967" title="Fluxo Comercial" prefix="$ " decimals={2} signed={true} subtitle="US$ milhões · Diária" icon="flow" />
  <KPITerminalCard data={externo_sgs} value="fluxo_fin" dateCol="d13970" code="SGS 13970" title="Fluxo Financeiro" prefix="$ " decimals={2} signed={true} subtitle="US$ milhões · Diária" icon="flow" />
</div>

```sql ptax_historico
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data
    FROM bcb_macro.ptax_daily
    WHERE moeda = 'USD'
)
SELECT
    p.data_referencia AS data,
    p.cotacao_venda,
    p.cotacao_compra
FROM bcb_macro.ptax_daily p
CROSS JOIN limite l
WHERE p.moeda = 'USD'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_cambio.value}' AS INTEGER)
ORDER BY p.data_referencia
```

<LineChart
    data={ptax_historico}
    x=data
    y=cotacao_venda
    title="Evolução histórica da PTAX de fechamento — USD/BRL"
    subtitle="ptax_daily · USD/BRL (boletim de fechamento)"
    yFmt=num2
    yGridlines=false
    xGridlines=false
    colorPalette={['#3b82f6']}
    chartAreaHeight=240
/>

```sql reservas_serie
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie = 13982
)
SELECT s.data, s.valor AS reservas_usd_mi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie = 13982
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_cambio.value}' AS INTEGER)
ORDER BY s.data
```

```sql fluxo_cambial_mensal
WITH limite AS (
    SELECT MAX(data) AS max_data FROM bcb_macro.sgs_series WHERE codigo_serie IN (13967, 13970)
)
SELECT
    date_trunc('month', s.data) AS mes,
    s.nome_serie AS segmento,
    SUM(s.valor) AS fluxo_usd_mi
FROM bcb_macro.sgs_series s CROSS JOIN limite l
WHERE s.codigo_serie IN (13967, 13970)
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_cambio.value}' AS INTEGER)
GROUP BY 1, 2
ORDER BY 1, 2
```

<Grid cols=2>
    <LineChart
        data={reservas_serie}
        x=data
        y=reservas_usd_mi
        title="Evolução das Reservas Internacionais (colchão externo)"
        subtitle="SGS 13982 · US$ milhões"
        yFmt=num0
        yGridlines=false
        xGridlines=false
        colorPalette={['#737373']}
    />
    <BarChart
        data={fluxo_cambial_mensal}
        x=mes
        y=fluxo_usd_mi
        series=segmento
        title="Fluxo financeiro concentra oscilações frente ao saldo comercial"
        subtitle="SGS 13967 (Comercial) vs SGS 13970 (Financeiro) · US$ milhões/mês"
        yFmt=num0
        type=grouped
        yGridlines=false
        xGridlines=false
        colorPalette={['#525252', '#3b82f6']}
    />
</Grid>

```sql ptax_tabela
SELECT
    data_referencia AS data,
    moeda,
    tipo_boletim,
    cotacao_compra,
    cotacao_venda,
    cotacao_venda - cotacao_compra AS spread
FROM bcb_macro.ptax_daily
WHERE moeda = 'USD'
ORDER BY data_referencia DESC
LIMIT 30
```

### Últimos Boletins PTAX Diários (USD)

<DataTable data={ptax_tabela} rows=10>
    <Column id=data title="Data" />
    <Column id=moeda title="Moeda" />
    <Column id=tipo_boletim title="Boletim" />
    <Column id=cotacao_compra title="Compra (R$)" fmt=num4 />
    <Column id=cotacao_venda title="Venda (R$)" fmt=num4 />
    <Column id=spread title="Spread (R$)" fmt=num4 />
</DataTable>
