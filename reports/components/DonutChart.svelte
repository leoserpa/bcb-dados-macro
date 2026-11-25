<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let nameCol = 'fonte';
  export let valueCol = 'registros';
  export let height = '210px';
  export let totalLabel = 'Registros';

  // SidraLake pre-attentive donut: #1 leader in Bloomberg Orange, remaining slices in neutral grays
  const palette = ['#ff6b00', '#737373', '#525252', '#3f3f46', '#2a2a2a'];

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: total = rows.reduce((sum, r) => sum + (Number(r[valueCol]) || 0), 0);

  $: items = rows.map((r, i) => {
    const val = Number(r[valueCol]) || 0;
    const pct = total > 0 ? (val / total) * 100 : 0;
    return {
      name: String(r[nameCol] ?? ''),
      value: val,
      pct,
      color: palette[i] || palette[palette.length - 1],
      isLeader: i === 0,
    };
  });

  function formatCompactTotal(n) {
    if (n >= 1_000_000) {
      return `${(n / 1_000_000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })} Mi`;
    }
    if (n >= 1_000) {
      return `${(n / 1_000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mil`;
    }
    return n.toLocaleString('pt-BR');
  }

  $: config = {
    backgroundColor: 'transparent',
    color: palette,
    tooltip: {
      trigger: 'item',
      backgroundColor: '#212121',
      borderColor: '#2a2a2a',
      borderWidth: 1,
      textStyle: {
        color: '#f5f5f5',
        fontFamily: 'IBM Plex Mono, ui-monospace, monospace',
        fontSize: 11,
      },
      formatter: (p) =>
        `${p.name}<br/><strong>${Number(p.value).toLocaleString('pt-BR')}</strong> (${String(p.percent).replace('.', ',')}%)`,
    },
    title: {
      text: formatCompactTotal(total),
      subtext: totalLabel,
      left: 'center',
      top: '39%',
      itemGap: 3,
      textStyle: {
        color: '#f5f5f5',
        fontFamily: 'Inter, IBM Plex Sans, system-ui, sans-serif',
        fontSize: 18,
        fontWeight: 700,
      },
      subtextStyle: {
        color: '#737373',
        fontFamily: 'IBM Plex Sans, system-ui, sans-serif',
        fontSize: 10.5,
        fontWeight: 500,
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['62%', '86%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: '#161616',
          borderWidth: 2,
        },
        label: { show: false },
        labelLine: { show: false },
        data: items.map((it) => ({ name: it.name, value: it.value })),
      },
    ],
  };
</script>

<div class="donut-layout">
  <div class="donut-chart-box">
    <ECharts {data} {config} {height} />
  </div>

  <ul class="donut-legend" aria-label="Distribuição por fonte">
    {#each items as item}
      <li class="donut-row">
        <span class="donut-name-wrap">
          <span class="donut-swatch" style={`background:${item.color};`} aria-hidden="true"></span>
          <span class="donut-name" class:is-leader={item.isLeader}>{item.name}</span>
        </span>
        <span class="donut-metrics">
          <span class="donut-count">{item.value.toLocaleString('pt-BR')}</span>
          <span class="donut-pct" class:is-leader={item.isLeader}>
            {item.pct.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
          </span>
        </span>
      </li>
    {/each}
  </ul>
</div>

<style>
  .donut-layout {
    display: grid;
    grid-template-columns: minmax(160px, 195px) minmax(0, 1fr);
    align-items: center;
    gap: 16px 20px;
    inline-size: 100%;
    min-inline-size: 0;
  }

  .donut-chart-box {
    inline-size: 100%;
    min-inline-size: 0;
  }

  .donut-legend {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-inline-size: 0;
  }

  .donut-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    min-inline-size: 0;
  }

  .donut-name-wrap {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-inline-size: 0;
  }

  .donut-swatch {
    inline-size: 8px;
    block-size: 8px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .donut-name {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    color: #a6a6a6;
    line-height: 1.3;
  }

  .donut-name.is-leader {
    color: #f5f5f5;
    font-weight: 600;
  }

  .donut-metrics {
    display: inline-flex;
    align-items: baseline;
    gap: 10px;
    flex-shrink: 0;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .donut-count {
    font-size: 11px;
    color: #737373;
  }

  .donut-pct {
    font-size: 12px;
    font-weight: 600;
    color: #d4d4d4;
    min-inline-size: 44px;
    text-align: right;
  }

  .donut-pct.is-leader {
    color: #ff6b00;
  }

  @media (max-width: 560px) {
    .donut-layout {
      grid-template-columns: 1fr;
      gap: 12px;
    }

    .donut-chart-box {
      max-inline-size: 210px;
      margin-inline: auto;
    }
  }
</style>
