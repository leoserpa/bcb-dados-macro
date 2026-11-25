<script>
  export let data = [];
  export let title = '';
  export let subtitle = '';
  export let columns = [];
  export let minWidth = '560px';
  export let marginBottom = false;

  const headingId = `cond-table-${Math.random().toString(36).slice(2, 9)}`;

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function formatCell(val, col) {
    if (val === null || val === undefined) return '—';
    const fmt = col.format || 'text';
    if (fmt === 'date') {
      if (val instanceof Date) return val.toISOString().slice(0, 10);
      return String(val).slice(0, 10);
    }
    if (fmt === 'freq') {
      const raw = String(val).toLowerCase();
      if (raw === 'diaria') return 'Diária';
      if (raw === 'mensal') return 'Mensal';
      if (raw === 'evento') return 'Evento';
      return String(val);
    }
    if (fmt === 'text' || fmt === 'id') {
      return String(val);
    }
    const num = Number(val);
    if (Number.isNaN(num)) return String(val);
    const signed = fmt.startsWith('signed');
    const digits = fmt.endsWith('0') ? 0 : fmt.endsWith('3') ? 3 : fmt.endsWith('4') ? 4 : 2;
    const sign = signed && num > 0 ? '+' : '';
    return `${sign}${num.toLocaleString('pt-BR', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })}`;
  }

  function cellTone(row, col) {
    if (col.toneCol && row[col.toneCol]) {
      return String(row[col.toneCol]);
    }
    if (col.alertCol && Number(row[col.alertCol]) === 1) {
      return 'alert';
    }
    return col.emphasis || 'default';
  }
</script>

<section
  class="terminal-panel cond-panel"
  class:has-mb={marginBottom}
  aria-labelledby={title ? headingId : undefined}
>
  {#if title}
    <h2 id={headingId} class="terminal-panel-title">{title}</h2>
  {/if}
  {#if subtitle}
    <p class="terminal-panel-sub">{subtitle}</p>
  {/if}

  <div class="cond-scroll" role="region" tabindex="0" aria-labelledby={title ? headingId : undefined}>
    <table class="cond-table" style={`min-inline-size: ${minWidth};`}>
      <thead>
        <tr>
          {#each columns as col}
            <th scope="col" class:num={col.align === 'right'}>{col.label}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr>
            {#each columns as col}
              {@const tone = cellTone(row, col)}
              <td
                class:num={col.align === 'right'}
                class:mono={col.mono !== false && col.format !== 'text' && col.format !== 'freq'}
                class:tone-alert={tone === 'alert'}
                class:tone-primary={tone === 'primary' || tone === 'neutral'}
                class:tone-muted={tone === 'muted'}
              >
                {formatCell(row[col.key], col)}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>

<style>
  .cond-panel.has-mb {
    margin-block-end: 18px;
  }

  .cond-scroll {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .cond-scroll:focus-visible {
    outline: 2px solid #ff6b00;
    outline-offset: 2px;
  }

  .cond-table {
    inline-size: 100%;
    border-collapse: collapse;
  }

  .cond-table thead th {
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
    white-space: nowrap;
  }

  .cond-table tbody td {
    padding: 9px 10px;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    color: #d4d4d4;
    border-block-end: 1px solid #202020;
    white-space: nowrap;
  }

  .cond-table tbody tr:last-child td {
    border-block-end: 0;
  }

  .cond-table .num {
    text-align: right;
  }

  .cond-table .mono {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .cond-table tbody td.tone-primary {
    color: #f5f5f5;
    font-weight: 500;
  }

  .cond-table tbody td.tone-muted {
    color: #737373;
    font-weight: 400;
  }

  .cond-table tbody td.tone-alert {
    color: #ff6b00 !important;
    font-weight: 600 !important;
  }
</style>
