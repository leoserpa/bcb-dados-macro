<script>
  export let data = [];
  export let value = null;
  export let dateCol = null;
  export let code = '';
  export let title = '';
  export let subtitle = '';
  export let prefix = '';
  export let suffix = '';
  export let decimals = 2;
  export let icon = 'trend';
  export let signed = false;

  $: row = data && data.length > 0 ? data[0] : null;
  $: rawVal = row && value ? row[value] : null;
  $: rawDate = row && dateCol ? row[dateCol] : '';

  function formatValue(v) {
    if (v === null || v === undefined) return '—';
    if (typeof v === 'string') return `${prefix}${v}${suffix}`;
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    const sign = signed && num > 0 ? '+' : '';
    const formatted = num.toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${prefix}${formatted}${suffix}`;
  }

  function formatDate(d) {
    if (!d) return '';
    if (d instanceof Date) return d.toISOString().slice(0, 10);
    return String(d).slice(0, 10);
  }
</script>

<div class="kpi-terminal-card">
  <div class="kpi-top">
    <div class="kpi-left">
      <span class="kpi-icon" aria-hidden="true">
        {#if icon === 'dollar'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {:else if icon === 'percent'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <line x1="19" y1="5" x2="5" y2="19" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" />
            <circle cx="6.5" cy="6.5" r="2.5" stroke="#A3A3A3" stroke-width="1.75" />
            <circle cx="17.5" cy="17.5" r="2.5" stroke="#A3A3A3" stroke-width="1.75" />
          </svg>
        {:else if icon === 'activity'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {:else if icon === 'bank'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {:else if icon === 'globe'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="#A3A3A3" stroke-width="1.75" />
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="#A3A3A3" stroke-width="1.75" />
          </svg>
        {:else if icon === 'alert'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {:else if icon === 'flow'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M7 16V4m0 0-4 4m4-4 4 4M17 8v12m0 0 4-4m-4 4-4-4" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {:else if icon === 'users'}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {:else}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path d="M3 3v18h18" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
            <path d="m19 9-5 5-4-4-3 3" stroke="#A3A3A3" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        {/if}
      </span>
      {#if code}
        <span class="kpi-code">{code}</span>
      {/if}
    </div>
    {#if rawDate}
      <span class="kpi-date">{formatDate(rawDate)}</span>
    {/if}
  </div>

  <div class="kpi-label">{title}</div>
  <div class="kpi-value">{formatValue(rawVal)}</div>
  {#if subtitle}
    <div class="kpi-sub">{subtitle}</div>
  {/if}
</div>

<style>
  .kpi-terminal-card {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
  }

  .kpi-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .kpi-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .kpi-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .kpi-code {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10px;
    font-weight: 600;
    color: #a3a3a3;
    background: #212121;
    padding: 2px 7px;
    border-radius: 5px;
    letter-spacing: 0.02em;
  }

  .kpi-date {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10px;
    color: #737373;
    white-space: nowrap;
  }

  .kpi-label {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #a3a3a3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .kpi-value {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 22px;
    font-weight: 700;
    color: #f5f5f5;
    line-height: 1.2;
    font-variant-numeric: tabular-nums;
  }

  .kpi-sub {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #737373;
  }
</style>
