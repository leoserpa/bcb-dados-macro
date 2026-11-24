---
title: Qualidade & Linhagem do Lakehouse
---

<div class="terminal-header">
  <div>
    <h1 class="terminal-title">Qualidade & Linhagem do Lakehouse</h1>
    <p class="terminal-subtitle">Governança Medallion (Bronze SHA-256 → Silver Parquet → Gold DuckDB) · Volumetria e frescor por tabela</p>
  </div>
  <div class="status-pills">
    <span class="status-pill"><span class="status-dot"></span>Quality Gates OK</span>
    <span class="status-pill">Cron: Seg–Sex 09:30 BRT</span>
  </div>
</div>

```sql lineage_kpis
SELECT
    SUM(registros) AS total_registros_gold,
    COUNT(*) AS total_tabelas,
    MAX(data_maxima) AS ultima_observacao
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
  <KPITerminalCard data={lineage_kpis} value="total_registros_gold" dateCol="ultima_observacao" code="SILVER→GOLD" title="Registros Consolidados" decimals={0} subtitle="SGS + Focus + Top5 + PTAX" icon="activity" />
  <KPITerminalCard data={sgs_cobertura_kpi} value="total_series_sgs" code="SGS" title="Séries Ativas BCB" decimals={0} subtitle="Diárias, mensais e evento" icon="trend" />
  <KPITerminalCard data={ptax_moedas_kpi} value="total_moedas_ptax" code="PTAX" title="Moedas Monitoradas" decimals={0} subtitle="Boletins de fechamento" icon="globe" />
  <KPITerminalCard data={lineage_kpis} value="total_tabelas" code="FONTES" title="Conjuntos Primários" decimals={0} subtitle="Upsert idempotente Parquet" icon="bank" />
  <KPITerminalCard data={lineage_kpis} value="ultima_observacao" code="FRESHNESS" title="Última Data de Dados" subtitle="Atualização automática útil" icon="flow" />
</div>

```sql lineage_tabela
SELECT
    tabela,
    fonte,
    registros,
    data_minima,
    data_maxima,
    CAST(ultima_ingestao AS VARCHAR) AS ultima_ingestao
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

<div class="terminal-panel" style="margin-bottom: 18px;">
  <div class="terminal-panel-title">Inventário das Tabelas Gold</div>
  <div class="terminal-panel-sub">vw_lakehouse_lineage · contagem de linhas e janelas temporais</div>
  <DataTable data={lineage_tabela} rows=10>
    <Column id=tabela title="Tabela" />
    <Column id=fonte title="Origem" />
    <Column id=registros title="Registros" fmt=num0 />
    <Column id=data_minima title="Data Mín." />
    <Column id=data_maxima title="Data Máx." />
  </DataTable>
</div>

<div class="terminal-panel">
  <div class="terminal-panel-title">Cobertura Completa — Todas as Séries SGS Ingeridas</div>
  <div class="terminal-panel-sub">sgs_series GROUP BY codigo_serie</div>
  <DataTable data={cobertura_sgs} rows=20>
    <Column id=codigo title="Série" />
    <Column id=serie title="Indicador" />
    <Column id=frequencia title="Frequência" />
    <Column id=observacoes title="Obs." fmt=num0 />
    <Column id=data_inicial title="Início" />
    <Column id=data_final title="Última Data" />
    <Column id=ultimo_valor title="Último Valor" fmt=num2 />
  </DataTable>
</div>
