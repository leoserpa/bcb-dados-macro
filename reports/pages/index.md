---
title: Panorama Macroeconômico — BCB
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Panorama Macroeconômico — Brasil</h1>
    <p class="page-subtitle">17 séries oficiais SGS · PTAX USD/EUR · Boletim Focus &amp; Top 5 · Leitura pré-atentiva</p>
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

      <ButtonGroup name=moeda_overview>
        <ButtonGroupItem valueLabel="USD" value="USD" default />
        <ButtonGroupItem valueLabel="EUR" value="EUR" />
      </ButtonGroup>
    </div>

    <div class="controls-right">
      <span class="status-chip"><span class="status-chip-accent">Atualização útil</span> · 09:30 BRT</span>
    </div>
  </div>
</div>

```sql kpi_sgs
SELECT
    MAX(CASE WHEN indicador_id = '432' THEN valor END) AS meta_selic,
    MAX(CASE WHEN indicador_id = '432' THEN data_observacao END) AS data_432,
    MAX(CASE WHEN indicador_id = '13522' THEN valor END) AS ipca_12m,
    MAX(CASE WHEN indicador_id = '13522' THEN data_observacao END) AS data_13522,
    MAX(CASE WHEN indicador_id = '13762' THEN valor END) AS dbgg_pib,
    MAX(CASE WHEN indicador_id = '13762' THEN data_observacao END) AS data_13762
FROM bcb_macro.vw_macro_latest
WHERE fonte = 'SGS'
```

```sql kpi_ptax
SELECT
    cotacao_venda,
    data_referencia
FROM bcb_macro.ptax_daily
WHERE moeda = '${inputs.moeda_overview}'
ORDER BY data_referencia DESC
LIMIT 1
```

```sql kpi_regime
SELECT
    data,
    juro_real_ex_ante,
    regime_monetario
FROM bcb_macro.vw_macro_regime
ORDER BY data DESC
LIMIT 1
```

<div class="kpi-grid-5">
  <KPITerminalCard data={kpi_sgs} value="meta_selic" dateCol="data_432" code="SGS 432" title="Meta Selic Copom" suffix="%" decimals={2} subtitle="SGS 432" icon="bank" />
  <KPITerminalCard data={kpi_sgs} value="ipca_12m" dateCol="data_13522" code="SGS 13522" title="IPCA Acum. 12m" suffix="%" decimals={2} subtitle="Meta 3,0%" icon="percent" />
  <KPITerminalCard data={kpi_ptax} value="cotacao_venda" dateCol="data_referencia" code="PTAX" title="PTAX Venda ({inputs.moeda_overview})" prefix="R$ " decimals={4} subtitle="Fechamento" icon="dollar" />
  <KPITerminalCard data={kpi_regime} value="juro_real_ex_ante" dateCol="data" code="JURO REAL" title="Juro Real Ex-Ante" suffix="%" decimals={2} signed={true} subtitle="Selic vs IPCA Focus" icon="activity" />
  <KPITerminalCard data={kpi_sgs} value="dbgg_pib" dateCol="data_13762" code="SGS 13762" title="DBGG / PIB" suffix="%" decimals={2} subtitle="Dívida bruta" icon="trend" />
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

```sql ptax_vs_focus
WITH limite AS (
    SELECT MAX(data_referencia) AS max_data
    FROM bcb_macro.ptax_daily
    WHERE moeda = '${inputs.moeda_overview}'
),
focus_ano AS (
    SELECT mediana_base0
    FROM bcb_macro.vw_focus_repricing
    WHERE indicador = 'Câmbio'
      AND TRY_CAST(data_referencia AS INTEGER) = (
          SELECT YEAR(MAX(data_base0)) FROM bcb_macro.vw_focus_repricing
      )
    LIMIT 1
)
SELECT
    p.data_referencia AS data,
    p.cotacao_venda AS ptax_venda,
    CASE WHEN '${inputs.moeda_overview}' = 'USD' THEN f.mediana_base0 ELSE NULL END AS consenso_focus
FROM bcb_macro.ptax_daily p
CROSS JOIN limite l
LEFT JOIN focus_ano f ON TRUE
WHERE p.moeda = '${inputs.moeda_overview}'
  AND date_diff('day', p.data_referencia, l.max_data) <= CAST('${inputs.horizonte_overview}' AS INTEGER)
ORDER BY p.data_referencia
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como evoluiu a Meta Selic nos últimos ciclos?</div>
    <div class="terminal-panel-sub">Taxa básica definida pelo Copom (% a.a.) · série em degrau</div>
    <TerminalLineChart
      data={selic_recente}
      x="data"
      y="meta_selic"
      labels={['Meta Selic']}
      suffix="%"
      decimals={2}
      step={true}
      height="245px"
    />
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Como a PTAX ({inputs.moeda_overview}/BRL) se comporta frente ao Focus?</div>
    <div class="terminal-panel-sub">Cotação diária de fechamento (laranja) frente à mediana anual do Focus (cinza, para USD)</div>
    <TerminalLineChart
      data={ptax_vs_focus}
      x="data"
      y={['ptax_venda', 'consenso_focus']}
      labels={['PTAX Venda', 'Consenso Focus']}
      colors={['#ff6b00', '#737373']}
      dashedIndices={[1]}
      prefix="R$ "
      decimals={2}
      height="245px"
    />
  </div>
</div>

```sql ipca_meta_overview
WITH limite AS (
    SELECT MAX(data) AS max_data
    FROM bcb_macro.sgs_series
    WHERE codigo_serie = 13522
)
SELECT
    s.data,
    s.valor AS ipca_12m,
    4.5 AS teto_meta,
    3.0 AS meta_cmn
FROM bcb_macro.sgs_series s
CROSS JOIN limite l
WHERE s.codigo_serie = 13522
  AND date_diff('day', s.data, l.max_data) <= CAST('${inputs.horizonte_overview}' AS INTEGER)
ORDER BY s.data
```

```sql juro_real_overview
WITH limite AS (
    SELECT MAX(data) AS max_data
    FROM bcb_macro.vw_juro_real_completo
)
SELECT
    j.data,
    j.juro_real_ex_ante,
    j.juro_real_ex_post
FROM bcb_macro.vw_juro_real_completo j
CROSS JOIN limite l
WHERE date_diff('day', j.data, l.max_data) <= CAST('${inputs.horizonte_overview}' AS INTEGER)
ORDER BY j.data
```

<div class="terminal-grid-2">
  <div class="terminal-panel">
    <div class="terminal-panel-title">O IPCA 12m está acima do teto da meta do CMN?</div>
    <div class="terminal-panel-sub">IPCA acumulado em 12 meses (laranja) vs teto 4,5% e centro 3,0% (cinza)</div>
    <TerminalLineChart
      data={ipca_meta_overview}
      x="data"
      y={['ipca_12m', 'teto_meta', 'meta_cmn']}
      labels={['IPCA 12m', 'Teto 4,5%', 'Meta 3,0%']}
      colors={['#ff6b00', '#737373', '#525252']}
      dashedIndices={[1, 2]}
      suffix="%"
      decimals={2}
      height="245px"
    />
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Qual a distância entre Juro Real Ex-Ante e Ex-Post?</div>
    <div class="terminal-panel-sub">Ex-Ante via IPCA Focus (laranja) vs Ex-Post via IPCA 12m realizado (cinza) · % a.a.</div>
    <TerminalLineChart
      data={juro_real_overview}
      x="data"
      y={['juro_real_ex_ante', 'juro_real_ex_post']}
      labels={['Juro Real Ex-Ante', 'Juro Real Ex-Post']}
      colors={['#ff6b00', '#737373']}
      suffix="%"
      decimals={2}
      height="245px"
    />
  </div>
</div>

```sql tabela_sgs_explorador
WITH regime_ult AS (
    SELECT juro_real_ex_ante, regime_monetario
    FROM bcb_macro.vw_macro_regime
    ORDER BY data DESC
    LIMIT 1
),
base AS (
    SELECT
        v.indicador_id AS codigo,
        v.indicador AS serie,
        CASE v.indicador_id
            WHEN '432' THEN 'Política Monetária'
            WHEN '11' THEN 'Política Monetária'
            WHEN '13522' THEN 'Inflação'
            WHEN '433' THEN 'Inflação'
            WHEN '189' THEN 'Inflação'
            WHEN '24369' THEN 'Trabalho'
            WHEN '24364' THEN 'Atividade'
            WHEN '13762' THEN 'Fiscal'
            WHEN '4513' THEN 'Fiscal'
            WHEN '5793' THEN 'Fiscal'
            WHEN '20631' THEN 'Crédito'
            WHEN '20714' THEN 'Crédito'
            WHEN '20783' THEN 'Crédito'
            WHEN '21082' THEN 'Crédito'
            ELSE 'Setor Externo'
        END AS dominio,
        v.detalhe AS frequencia,
        v.data_observacao AS ultima_data,
        v.valor,
        CASE v.indicador_id
            WHEN '432' THEN concat('Juro real ', printf('%+.2f%%', r.juro_real_ex_ante))
            WHEN '13522' THEN 'Teto CMN 4,50%'
            WHEN '13762' THEN 'Ref. 80,0% PIB'
            WHEN '4513' THEN '% do PIB'
            WHEN '5793' THEN 'Meta 0,0% PIB'
            WHEN '11' THEN '% ao dia'
            WHEN '433' THEN 'Var. mensal'
            WHEN '189' THEN 'FGV mensal'
            WHEN '24369' THEN 'Trim. móvel'
            WHEN '24364' THEN 'Índice dessaz.'
            WHEN '20631' THEN 'R$ bilhões'
            WHEN '20714' THEN 'Média % a.a.'
            WHEN '20783' THEN 'Spread médio'
            WHEN '21082' THEN 'Ref. 5,00%'
            WHEN '13982' THEN 'US$ bilhões'
            ELSE 'US$ milhões'
        END AS referencia,
        CASE
            WHEN v.indicador_id = '432' THEN r.regime_monetario
            WHEN v.indicador_id = '13522' AND v.valor > 4.5 THEN 'Acima Teto'
            WHEN v.indicador_id = '13522' AND v.valor < 1.5 THEN 'Abaixo Piso'
            WHEN v.indicador_id = '13522' THEN 'Na Meta'
            WHEN v.indicador_id = '13762' AND v.valor >= 80.0 THEN 'Atenção'
            WHEN v.indicador_id = '21082' AND v.valor >= 5.0 THEN 'Atenção'
            WHEN v.indicador_id = '5793' AND v.valor < 0.0 THEN 'Déficit'
            WHEN v.indicador_id = '5793' THEN 'Superávit'
            ELSE 'Normal'
        END AS situacao
    FROM bcb_macro.vw_macro_latest v
    CROSS JOIN regime_ult r
    WHERE v.fonte = 'SGS'
)
SELECT
    codigo,
    serie,
    dominio,
    frequencia,
    ultima_data,
    valor,
    referencia,
    situacao,
    CASE WHEN situacao IN ('Restritivo', 'Acima Teto', 'Abaixo Piso', 'Atenção', 'Déficit') THEN 1 ELSE 0 END AS alerta
FROM base
ORDER BY alerta DESC, CAST(codigo AS INTEGER)
```

<ExecutiveTable
  data={tabela_sgs_explorador}
  title="Explorador Executivo — Todas as 17 Séries Oficiais SGS"
  subtitle="Últimas observações oficiais · Destaque tipográfico apenas nos desvios de regime ou meta"
/>

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

<ConditionalTable
  data={focus_resumo}
  title="Consenso Boletim Focus — Projeções Anuais (Base {inputs.base_focus})"
  subtitle="Medianas mais recentes das expectativas de mercado para os próximos 4 exercícios"
  minWidth="480px"
  columns={[
    { key: 'indicador', label: 'Indicador', format: 'text', emphasis: 'primary' },
    { key: 'ano', label: 'Ano', format: 'id', emphasis: 'muted' },
    { key: 'data_coleta', label: 'Coleta', format: 'date', emphasis: 'muted' },
    { key: 'mediana', label: 'Mediana', align: 'right', format: 'focusVal', emphasis: 'primary' }
  ]}
/>
