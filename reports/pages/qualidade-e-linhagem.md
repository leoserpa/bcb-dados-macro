---
title: Qualidade & Linhagem do Lakehouse
---

<div class="page-hero">
  <div class="page-title-group">
    <h1 class="page-title">Qualidade & Linhagem do Lakehouse</h1>
    <p class="page-subtitle">Governança Medallion (Bronze SHA-256 → Silver Parquet → Gold DuckDB), volumetria e frescor dos dados</p>
  </div>

  <div class="controls-bar">
    <div class="controls-left">
      <span class="status-chip"><span class="status-chip-dot"></span>Quality Gates Ativos</span>
      <span class="status-chip">Agendamento: Seg–Sex 09:30 BRT</span>
    </div>
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
  <KPITerminalCard data={lineage_kpis} value="total_registros_gold" title="Registros Consolidados" decimals={0} subtitle="SGS + Focus + Top5 + PTAX" accent={true} />
  <KPITerminalCard data={sgs_cobertura_kpi} value="total_series_sgs" title="Séries Ativas SGS" decimals={0} subtitle="Diárias, mensais e evento" accent={true} />
  <KPITerminalCard data={ptax_moedas_kpi} value="total_moedas_ptax" title="Moedas PTAX" decimals={0} subtitle="USD e EUR Fechamento" />
  <KPITerminalCard data={lineage_kpis} value="total_tabelas" title="Conjuntos Primários" decimals={0} subtitle="Upsert idempotente Parquet" />
  <KPITerminalCard data={lineage_kpis} value="ultima_observacao" title="Última Data de Dados" subtitle="Atualização automática útil" accent={true} />
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
    MAX(data) AS data_final,
    arg_max(valor, data) AS ultimo_valor
FROM bcb_macro.sgs_series
GROUP BY 1, 2, 3
ORDER BY 1
```

<div class="terminal-grid-asym-wide">
  <div class="terminal-stack">
    <div class="terminal-panel">
      <div class="terminal-panel-title">Distribuição de Registros por Origem</div>
      <div class="terminal-panel-sub">Participação de cada conjunto primário na camada analítica Gold</div>
      <DonutChart data={lineage_donut} nameCol="fonte" valueCol="registros" height="235px" />
    </div>

    <div class="terminal-panel">
      <div class="terminal-panel-title">Inventário das Tabelas Gold</div>
      <div class="terminal-panel-sub">Contagem de linhas e janela temporal por tabela</div>
      <DataTable data={lineage_tabela} rows=10>
        <Column id=tabela title="Tabela" />
        <Column id=fonte title="Origem" />
        <Column id=registros title="Registros" fmt=num0 />
        <Column id=data_maxima title="Última Data" />
      </DataTable>
    </div>
  </div>

  <div class="terminal-panel">
    <div class="terminal-panel-title">Cobertura Completa — Todas as 17 Séries SGS</div>
    <div class="terminal-panel-sub">Frequência, volume de observações e último valor ingerido</div>
    <DataTable data={cobertura_sgs} rows=20>
      <Column id=codigo title="Série" />
      <Column id=serie title="Indicador" />
      <Column id=frequencia title="Freq." />
      <Column id=observacoes title="Obs." fmt=num0 />
      <Column id=ultimo_valor title="Último" fmt=num2 />
    </DataTable>
  </div>
</div>
