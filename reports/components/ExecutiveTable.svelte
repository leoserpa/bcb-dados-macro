<script>
  export let data = [];
  export let title = 'Explorador Executivo — Todas as 17 Séries SGS';
  export let subtitle = 'Últimas observações oficiais da camada Gold · Formatação condicional tipográfica';

  let query = '';

  $: rawRows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: filteredRows = query.trim()
    ? rawRows.filter((r) => {
        const q = query.trim().toLowerCase();
        return (
          String(r.codigo ?? '').toLowerCase().includes(q) ||
          String(r.serie ?? '').toLowerCase().includes(q) ||
          String(r.dominio ?? '').toLowerCase().includes(q) ||
          String(r.situacao ?? '').toLowerCase().includes(q)
        );
      })
    : rawRows;

  function formatFreq(f) {
    const raw = String(f ?? '').toLowerCase();
    if (raw === 'diaria') return 'Diária';
    if (raw === 'mensal') return 'Mensal';
    if (raw === 'evento') return 'Evento';
    return f ?? '—';
  }

  function formatDate(d) {
    if (!d) return '—';
    if (d instanceof Date) return d.toISOString().slice(0, 10);
    return String(d).slice(0, 10);
  }

  function formatValue(val, codigo) {
    if (val === null || val === undefined) return '—';
    const num = Number(val);
    if (Number.isNaN(num)) return String(val);
    const id = String(codigo);
    if (id === '11') {
      return `${num.toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })}%`;
    }
    if (id === '13982') {
      return `US$ ${(num / 1000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} bi`;
    }
    if (id === '20631') {
      return `R$ ${(num / 1000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} bi`;
    }
    if (id === '13967' || id === '13970') {
      const sign = num < 0 ? '-' : num > 0 ? '+' : '';
      return `${sign}US$ ${Math.abs(num).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} mi`;
    }
    if (id === '24364') {
      return num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    if (id === '20783') {
      return `${num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} pp`;
    }
    const sign = id === '5793' && num > 0 ? '+' : '';
    return `${sign}${num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
  }

  function exportCsv() {
    if (!filteredRows.length) return;
    const headers = ['codigo', 'serie', 'dominio', 'frequencia', 'ultima_data', 'valor', 'referencia', 'situacao'];
    const lines = [headers.join(',')];
    for (const r of filteredRows) {
      const vals = headers.map((h) => {
        const raw = h === 'ultima_data' ? formatDate(r[h]) : r[h] ?? '';
        const str = String(raw).replace(/"/g, '""');
        return `"${str}"`;
      });
      lines.push(vals.join(','));
    }
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bcb_macro_series_sgs.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
</script>

<section class="terminal-panel exec-explorer" aria-labelledby="exec-explorer-title">
  <div class="exec-head">
    <div>
      <h2 id="exec-explorer-title" class="terminal-panel-title">{title}</h2>
      <p class="terminal-panel-sub" style="margin-block-end: 0;">{subtitle}</p>
    </div>

    <div class="exec-actions">
      <input
        type="search"
        class="exec-search"
        bind:value={query}
        placeholder="Buscar série ou indicador..."
        aria-label="Buscar série ou indicador"
      />
      <button type="button" class="exec-export" on:click={exportCsv}>Exportar CSV</button>
    </div>
  </div>

  <div class="exec-table-scroll" role="region" tabindex="0" aria-labelledby="exec-explorer-title">
    <table class="exec-table">
      <thead>
        <tr>
          <th scope="col">Série</th>
          <th scope="col">Indicador</th>
          <th scope="col">Domínio</th>
          <th scope="col">Frequência</th>
          <th scope="col">Última Data</th>
          <th scope="col" class="num">Valor</th>
          <th scope="col" class="num">Referência</th>
          <th scope="col" class="num">Situação</th>
        </tr>
      </thead>
      <tbody>
        {#each filteredRows as row}
          <tr>
            <td class="mono muted">{row.codigo}</td>
            <td class="ind">{row.serie}</td>
            <td class="muted">{row.dominio}</td>
            <td class="muted">{formatFreq(row.frequencia)}</td>
            <td class="mono muted">{formatDate(row.ultima_data)}</td>
            <td class="mono num val">{formatValue(row.valor, row.codigo)}</td>
            <td class="mono num muted">{row.referencia}</td>
            <td class="num status" class:is-alert={Number(row.alerta) === 1}>{row.situacao}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <div class="exec-foot">
    <span>Mostrando {filteredRows.length} de {rawRows.length} séries oficiais SGS</span>
  </div>
</section>

<style>
  .exec-explorer {
    margin-block-end: 18px;
  }

  .exec-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px 16px;
    margin-block-end: 14px;
  }

  .exec-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .exec-search {
    min-block-size: max(34px, var(--target-size));
    inline-size: min(240px, 100%);
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #2a2a2a;
    background: #0f0f0f;
    color: #f5f5f5;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
  }

  .exec-search::placeholder {
    color: #575757;
  }

  .exec-search:focus-visible,
  .exec-export:focus-visible,
  .exec-table-scroll:focus-visible {
    outline: 2px solid #ff6b00;
    outline-offset: 2px;
  }

  .exec-export {
    min-block-size: max(34px, var(--target-size));
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid #2a2a2a;
    background: #212121;
    color: #f5f5f5;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
  }

  .exec-export:hover {
    background: #2a2a2a;
  }

  .exec-table-scroll {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .exec-table {
    inline-size: 100%;
    min-inline-size: 760px;
    border-collapse: collapse;
  }

  .exec-table thead th {
    text-align: left;
    padding: 9px 10px;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #737373;
    border-block-end: 1px solid #202020;
    background: #161616;
    position: sticky;
    inset-block-start: 0;
  }

  .exec-table tbody td {
    padding: 10px 10px;
    font-size: 12px;
    border-block-end: 1px solid #202020;
    white-space: nowrap;
  }

  .exec-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .exec-table .ind {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-weight: 500;
    color: #f5f5f5;
  }

  .exec-table .mono {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .exec-table .muted {
    color: #737373;
  }

  .exec-table .num {
    text-align: right;
  }

  .exec-table .val {
    font-weight: 600;
    color: #f5f5f5;
  }

  .exec-table tbody td.status {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11.5px;
    font-weight: 400;
    color: #737373;
  }

  .exec-table tbody td.status.is-alert {
    font-weight: 600 !important;
    color: #ff6b00 !important;
  }

  .exec-foot {
    margin-block-start: 12px;
    padding-block-start: 10px;
    border-block-start: 1px solid #202020;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #575757;
  }

  @media (max-width: 640px) {
    .exec-actions {
      inline-size: 100%;
    }
    .exec-search {
      flex: 1 1 160px;
    }
  }
</style>
