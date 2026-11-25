<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let x = 'data';
  export let y = [];
  export let labels = [];
  export let colors = ['#ff6b00', '#737373', '#525252'];
  export let dashedIndices = [];
  export let step = false;
  export let prefix = '';
  export let suffix = '';
  export let decimals = 2;
  export let signed = false;
  export let height = '240px';
  export let showEndLabel = true;

  const MONTHS_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  $: yCols = Array.isArray(y) ? y : y ? [y] : [];

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  function toIsoDate(d) {
    if (d instanceof Date) return d.toISOString().slice(0, 10);
    return String(d ?? '').slice(0, 10);
  }

  function formatVal(v) {
    if (v === null || v === undefined) return '—';
    const num = Number(v);
    if (Number.isNaN(num)) return String(v);
    const sign = signed && num > 0 ? '+' : '';
    const formatted = num.toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    return `${sign}${prefix}${formatted}${suffix}`;
  }

  function formatAxisDate(ts) {
    const dt = new Date(ts);
    if (Number.isNaN(dt.getTime())) return String(ts);
    const m = MONTHS_PT[dt.getUTCMonth()];
    const yr = dt.getUTCFullYear();
    return dt.getUTCMonth() === 0 ? String(yr) : `${m} ${yr}`;
  }

  function prettifyName(col) {
    return String(col)
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  $: builtSeries = yCols
    .map((col, idx) => {
      const pts = [];
      let lastPt = null;
      for (const r of rows) {
        const rawX = r[x];
        const rawY = r[col];
        if (rawX === null || rawX === undefined) continue;
        const iso = toIsoDate(rawX);
        if (rawY === null || rawY === undefined || rawY === '') {
          pts.push([iso, null]);
        } else {
          const num = Number(rawY);
          if (!Number.isNaN(num)) {
            pts.push([iso, num]);
            lastPt = { x: iso, val: num };
          }
        }
      }
      if (!lastPt) return null;

      const color = colors[idx] || colors[colors.length - 1] || '#737373';
      const isPrimary = idx === 0;
      const isDashed = Array.isArray(dashedIndices) && dashedIndices.includes(idx);
      const name = labels[idx] || prettifyName(col);

      return {
        name,
        type: 'line',
        data: pts,
        showSymbol: false,
        smooth: false,
        step: step && isPrimary ? 'end' : false,
        connectNulls: true,
        lineStyle: {
          color,
          width: isPrimary ? 2 : 1.35,
          type: isDashed ? 'dashed' : 'solid',
        },
        itemStyle: { color },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color,
            borderColor: '#161616',
            borderWidth: 2,
          },
        },
        markPoint:
          isPrimary && showEndLabel
            ? {
                symbol: 'circle',
                symbolSize: 8,
                silent: true,
                itemStyle: {
                  color,
                  borderColor: '#161616',
                  borderWidth: 2,
                },
                label: {
                  show: true,
                  position: 'top',
                  distance: 7,
                  align: 'right',
                  formatter: () => formatVal(lastPt.val),
                  color,
                  fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
                  fontWeight: 700,
                  fontSize: 11.5,
                  backgroundColor: 'rgba(22, 22, 22, 0.88)',
                  padding: [2, 5],
                  borderRadius: 4,
                },
                data: [{ coord: [lastPt.x, lastPt.val] }],
              }
            : undefined,
      };
    })
    .filter(Boolean);

  $: hasLegend = builtSeries.length > 1;

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 300,
    grid: {
      top: hasLegend ? 38 : 28,
      right: 18,
      bottom: 24,
      left: 10,
      containLabel: true,
    },
    legend: hasLegend
      ? {
          show: true,
          top: 0,
          left: 'center',
          icon: 'circle',
          itemWidth: 8,
          itemHeight: 8,
          itemGap: 14,
          textStyle: {
            color: '#a6a6a6',
            fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
            fontSize: 11,
          },
        }
      : { show: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#212121',
      borderColor: '#2a2a2a',
      borderWidth: 1,
      textStyle: {
        color: '#f5f5f5',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 11,
      },
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: '#3f3f46',
          width: 1,
          type: 'dashed',
        },
      },
      formatter: (params) => {
        if (!Array.isArray(params) || !params.length) return '';
        const dateStr = toIsoDate(params[0].axisValueLabel || params[0].value?.[0]);
        const lines = [`<div style="color:#a6a6a6;margin-bottom:4px;">${dateStr}</div>`];
        for (const p of params) {
          const v = Array.isArray(p.value) ? p.value[1] : p.value;
          if (v === null || v === undefined) continue;
          lines.push(
            `<div style="display:flex;justify-content:space-between;gap:14px;">` +
              `<span><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${p.color};margin-right:6px;"></span>${p.seriesName}</span>` +
              `<strong style="color:#f5f5f5;">${formatVal(v)}</strong>` +
            `</div>`
          );
        }
        return lines.join('');
      },
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#2a2a2a' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#737373',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 10.5,
        hideOverlap: true,
        formatter: (val) => formatAxisDate(val),
      },
    },
    yAxis: {
      type: 'value',
      scale: true,
      max: (extent) => {
        if (!Number.isFinite(extent.max) || !Number.isFinite(extent.min)) return undefined;
        const span = extent.max - extent.min;
        const pad = span > 0 ? span * 0.18 : Math.abs(extent.max || 1) * 0.14;
        return Number((extent.max + pad).toFixed(4));
      },
      min: (extent) => {
        if (!Number.isFinite(extent.max) || !Number.isFinite(extent.min)) return undefined;
        const span = extent.max - extent.min;
        const pad = span > 0 ? span * 0.08 : Math.abs(extent.min || 1) * 0.08;
        return Number((extent.min - pad).toFixed(4));
      },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        color: '#737373',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 10.5,
        formatter: (val) => formatVal(val),
      },
    },
    series: builtSeries,
  };
</script>

<div class="terminal-line-wrap">
  <ECharts {data} {config} {height} />
</div>

<style>
  .terminal-line-wrap {
    inline-size: 100%;
    min-inline-size: 0;
  }
</style>
