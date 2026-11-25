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
  export let accent = false;
  export let icon = '';

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

  $: metaText = [subtitle, rawDate ? formatDate(rawDate) : ''].filter(Boolean).join(' · ');
</script>

<div class="kpi-card" data-code={code || undefined} data-icon={icon || undefined}>
  <div class="kpi-label">{title}</div>
  <div class="kpi-value">{formatValue(rawVal)}</div>
  {#if metaText}
    <div class="kpi-meta" class:is-accent={accent}>{metaText}</div>
  {/if}
</div>

<style>
  .kpi-card {
    background: #161616;
    border: 1px solid #282828;
    border-radius: 8px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 5px;
    min-inline-size: 0;
    min-block-size: 86px;
  }

  .kpi-label {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11px;
    font-weight: 400;
    color: #737373;
    line-height: 1.3;
  }

  .kpi-value {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: clamp(18px, 1.8vw, 22px);
    font-weight: 700;
    color: #f5f5f5;
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
  }

  .kpi-meta {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10px;
    font-weight: 500;
    color: #575757;
    line-height: 1.3;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .kpi-meta.is-accent {
    color: #60a5fa;
  }

  @media (max-width: 640px) {
    .kpi-card {
      padding: 12px 13px;
      min-block-size: 78px;
    }
  }
</style>
