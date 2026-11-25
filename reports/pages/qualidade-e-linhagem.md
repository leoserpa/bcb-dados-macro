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
    CAST(MAX(data_maxima) AS VARCHAR) AS ultima_observacao
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
SELECT
    codigo_serie AS codigo,
    nome_serie AS serie,
    frequencia,
    COUNT(*) AS observacoes,
    MIN(data) AS data_inicial,
    MAX(data) AS data_final,
    arg_max(valor, data) AS ultimo_valor
FROM bcb_macro.sgs_series
GROUP BY 1, 2, 3
ORDER BY 1
```

<div class="terminal-grid-asym">
  <div class="terminal-stack">
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

  <div class="terminal-panel">
    <div class="terminal-panel-title">Cobertura Completa — Todas as 17 Séries SGS</div>
    <div class="terminal-panel-sub">Volume de observações, janela histórica e último valor oficial por série</div>
    <DataTable data={cobertura_sgs} rows=20>
      <Column id=codigo title="Série" />
      <Column id=serie title="Indicador" />
      <Column id=frequencia title="Freq." />
      <Column id=observacoes title="Obs." fmt=num0 />
      <Column id=data_inicial title="Início" />
      <Column id=data_final title="Último" />
      <Column id=ultimo_valor title="Valor" fmt=num2 />
    </DataTable>
  </div>
</div>
