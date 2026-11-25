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
  export let signed = false;
  export let icon = 'trend';

  $: row = data && data.length > 0 ? data[0] : null;
  $: rawVal = row && value ? row[value] : null;
  $: rawDate = row && dateCol ? row[dateCol] : '';

  function formatValue(v) {
    if (v === null || v === undefined) return '—';
    if (v instanceof Date) return v.toISOString().slice(0, 10);
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

  $: metaText = [subtitle, rawDate ? formatDate(rawDate) : ''].filter(Boolean).join(' · ');
</script>

<div class="kpi-card" data-code={code || undefined}>
  <div class="kpi-head">
    <span class="kpi-label">{title}</span>
    <span class="kpi-icon" aria-hidden="true">
      {#if icon === 'dollar'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'percent'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <line x1="19" y1="5" x2="5" y2="19" stroke="#737373" stroke-width="1.6" stroke-linecap="round" />
          <circle cx="6.5" cy="6.5" r="2.2" stroke="#737373" stroke-width="1.6" />
          <circle cx="17.5" cy="17.5" r="2.2" stroke="#737373" stroke-width="1.6" />
        </svg>
      {:else if icon === 'activity'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'bank'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'globe'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="9.5" stroke="#737373" stroke-width="1.6" />
          <path d="M2.5 12h19M12 2.5a14 14 0 0 1 3.8 9.5 14 14 0 0 1-3.8 9.5 14 14 0 0 1-3.8-9.5 14 14 0 0 1 3.8-9.5z" stroke="#737373" stroke-width="1.6" />
        </svg>
      {:else if icon === 'alert'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'flow'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M7 16V4m0 0-4 4m4-4 4 4M17 8v12m0 0 4-4m-4 4-4-4" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else if icon === 'users'}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {:else}
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M3 3v18h18" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          <path d="m19 9-5 5-4-4-3 3" stroke="#737373" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      {/if}
    </span>
  </div>

  <div class="kpi-value">{formatValue(rawVal)}</div>

  {#if metaText}
    <div class="kpi-sub">{metaText}</div>
  {/if}
</div>

<style>
  .kpi-card {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
    min-inline-size: 0;
    min-block-size: 104px;
  }

  .kpi-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .kpi-label {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #a6a6a6;
    line-height: 1.25;
  }

  .kpi-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .kpi-value {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: clamp(19px, 1.85vw, 24px);
    font-weight: 700;
    color: #f5f5f5;
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
  }

  .kpi-sub {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #737373;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  @media (max-width: 640px) {
    .kpi-card {
      padding: 13px 14px;
      min-block-size: 92px;
    }
  }
</style>
