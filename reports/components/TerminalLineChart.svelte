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

  $: seriesMeta = yCols
    .map((col, idx) => {
      const pts = [];
      let lastPt = null;
      for (const r of rows) {
        const rawX = r[x];
        const rawY = r[col];
        if (rawX === null || rawX === undefined) continue;
        const iso = toIsoDate(rawX);
        if (rawY !== null && rawY !== undefined && rawY !== '') {
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
      const endText = formatVal(lastPt.val);

      return {
        endText,
        series: {
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
          endLabel: showEndLabel
            ? {
                show: true,
                distance: 10,
                formatter: () => endText,
                color: isPrimary ? color : '#a6a6a6',
                fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
                fontWeight: isPrimary ? 700 : 500,
                fontSize: isPrimary ? 11.5 : 10.5,
              }
            : { show: false },
          labelLayout: showEndLabel ? { moveOverlap: 'shiftY' } : undefined,
          markPoint: showEndLabel
            ? {
                symbol: 'circle',
                symbolSize: isPrimary ? 8 : 5,
                silent: true,
                label: { show: false },
                itemStyle: {
                  color,
                  borderColor: '#161616',
                  borderWidth: isPrimary ? 2 : 1.5,
                },
                data: [{ coord: [lastPt.x, lastPt.val] }],
              }
            : undefined,
        },
      };
    })
    .filter(Boolean);

  $: builtSeries = seriesMeta.map((m) => m.series);
  $: hasLegend = builtSeries.length > 1;
  $: maxEndChars = seriesMeta.reduce((acc, m) => Math.max(acc, m.endText.length), 6);
  $: rightPad = showEndLabel ? Math.max(62, maxEndChars * 8 + 20) : 16;

  $: config = {
    backgroundColor: 'transparent',
    animationDuration: 300,
    grid: {
      top: hasLegend ? 36 : 20,
      right: rightPad,
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
            padding: [0, 0, 0, 3],
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
      boundaryGap: ['8%', '12%'],
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
