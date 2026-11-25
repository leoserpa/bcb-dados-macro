---
title: Qualidade & Linhagem do Lakehouse
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Qualidade &amp; Linhagem do Lakehouse</h1>
    <p class="page-subtitle">Arquitetura Medallion (Bronze SHA-256 → Silver Parquet → Gold DuckDB) · Volumetria e frescor por fonte</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <span class="status-chip"><span class="status-chip-accent">Quality Gates OK</span> · Contrato validado</span>
      <span class="status-chip">Pipeline diário · Seg–Sex 09:30 BRT</span>
    </div>
  </div>
</div>

```sql lineage_kpis
SELECT
    SUM(registros) AS total_registros_gold,
    COUNT(*) AS total_tabelas,
    LEFT(CAST(MAX(data_maxima) AS VARCHAR), 10) AS ultima_observacao
FROM bcb_macro.vw_lakehouse_lineage
WHERE tabela IN ('sgs_series', 'focus_expectations', 'focus_top5', 'ptax_quotes')
```

```sql sgs_cobertura_kpi
SELECT COUNT(DISTINCT codigo_serie) AS total_series_sgs
FROM bcb_macro.sgs_series
```

```sql ptax_moedas_kpi
SELECT COUNT(DISTINCT moeda) AS total_moedas_ptax
FROM bcb_macro.ptax_daily
```

<div class="kpi-grid-5">
  <KPITerminalCard data={lineage_kpis} value="total_registros_gold" code="SILVER→GOLD" title="Registros Consolidados" decimals={0} subtitle="SGS + Focus + Top 5 + PTAX" icon="activity" />
  <KPITerminalCard data={sgs_cobertura_kpi} value="total_series_sgs" code="SGS" title="Séries Ativas BCB" decimals={0} subtitle="Diárias, mensais e evento" icon="trend" />
  <KPITerminalCard data={ptax_moedas_kpi} value="total_moedas_ptax" code="PTAX" title="Moedas Monitoradas" decimals={0} subtitle="USD e EUR · Fechamento" icon="globe" />
  <KPITerminalCard data={lineage_kpis} value="total_tabelas" code="FONTES" title="Conjuntos Primários" decimals={0} subtitle="Upsert idempotente Parquet" icon="bank" />
  <KPITerminalCard data={lineage_kpis} value="ultima_observacao" code="FRESHNESS" title="Última Data de Dados" subtitle="Atualização automática útil" icon="flow" />
</div>

```sql lineage_donut
SELECT
    fonte,
    registros
FROM bcb_macro.vw_lakehouse_lineage
WHERE tabela IN ('sgs_series', 'focus_expectations', 'focus_top5', 'ptax_quotes')
ORDER BY registros DESC
```

```sql lineage_tabela
SELECT
    tabela,
    fonte,
    registros,
    data_minima,
    data_maxima
FROM bcb_macro.vw_lakehouse_lineage
ORDER BY registros DESC
```

```sql cobertura_sgs
WITH ref AS (
    SELECT MAX(data) AS max_ref FROM bcb_macro.sgs_series
),
agg AS (
    SELECT
        codigo_serie,
        CAST(CAST(codigo_serie AS BIGINT) AS VARCHAR) AS codigo,
        nome_serie AS serie,
        frequencia,
        COUNT(*) AS observacoes,
        MIN(data) AS data_inicial,
        MAX(data) AS data_final,
        arg_max(valor, data) AS ultimo_valor,
        date_diff('day', MAX(data), (SELECT max_ref FROM ref)) AS dias_defasagem
    FROM bcb_macro.sgs_series
    GROUP BY codigo_serie, nome_serie, frequencia
)
SELECT
    codigo,
    serie,
    frequencia,
    observacoes,
    data_inicial,
    data_final,
    ultimo_valor,
    CASE
        WHEN (frequencia = 'mensal' AND dias_defasagem > 95)
          OR (frequencia <> 'mensal' AND dias_defasagem > 10)
        THEN 'Atraso'
        ELSE 'Em dia'
    END AS sla_status,
    CASE
        WHEN (frequencia = 'mensal' AND dias_defasagem > 95)
          OR (frequencia <> 'mensal' AND dias_defasagem > 10)
        THEN 1
        ELSE 0
    END AS alerta_atraso
FROM agg
ORDER BY codigo_serie
```

<div class="terminal-grid-donut">
  <div class="terminal-panel">
    <div class="terminal-panel-title">Como os registros se distribuem por fonte oficial?</div>
    <div class="terminal-panel-sub">Participação dos quatro conjuntos primários ingeridos na camada Silver</div>
    <DonutChart data={lineage_donut} nameCol="fonte" valueCol="registros" height="240px" />
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Inventário das Tabelas Analíticas</div>
    <div class="terminal-panel-sub">Contagem de registros e janelas temporais disponíveis no catálogo</div>
    <DataTable data={lineage_tabela} rows=10>
      <Column id=tabela title="Conjunto" />
      <Column id=fonte title="Origem" />
      <Column id=registros title="Registros" fmt=num0 />
      <Column id=data_minima title="Início" />
      <Column id=data_maxima title="Último" />
    </DataTable>
  </div>
</div>

<ConditionalTable
  data={cobertura_sgs}
  title="Cobertura Completa — Todas as 17 Séries SGS"
  subtitle="Volume histórico, frescor e monitoramento de SLA (alerta em laranja apenas se exceder o prazo de publicação)"
  minWidth="740px"
  columns={[
    { key: 'codigo', label: 'Série', format: 'id', emphasis: 'muted' },
    { key: 'serie', label: 'Indicador', format: 'text', emphasis: 'primary' },
    { key: 'frequencia', label: 'Frequência', format: 'freq', emphasis: 'muted' },
    { key: 'observacoes', label: 'Obs.', align: 'right', format: 'num0', emphasis: 'muted' },
    { key: 'data_inicial', label: 'Início', format: 'date', emphasis: 'muted' },
    { key: 'data_final', label: 'Última Data', format: 'date', emphasis: 'muted', alertCol: 'alerta_atraso' },
    { key: 'ultimo_valor', label: 'Último Valor', align: 'right', format: 'num2', emphasis: 'primary' },
    { key: 'sla_status', label: 'SLA', align: 'right', format: 'text', emphasis: 'muted', alertCol: 'alerta_atraso' }
  ]}
/>
