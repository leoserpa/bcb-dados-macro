<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let nameCol = 'fonte';
  export let valueCol = 'registros';
  export let height = '240px';

  // SidraLake pre-attentive donut: #1 leader in Bloomberg Orange, remaining slices in neutral grays
  const palette = ['#ff6b00', '#737373', '#525252', '#3f3f46', '#2a2a2a'];

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: seriesData = rows.map((r) => ({
    name: String(r[nameCol] ?? ''),
    value: Number(r[valueCol] ?? 0),
  }));

  $: config = {
    backgroundColor: 'transparent',
    color: palette,
    tooltip: {
      trigger: 'item',
      backgroundColor: '#191c1d',
      borderColor: '#2b2f30',
      textStyle: {
        color: '#f5f5f5',
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 11,
      },
      formatter: (p) => `${p.name}: ${Number(p.value).toLocaleString('pt-BR')} (${p.percent}%)`,
    },
    legend: {
      bottom: 0,
      left: 'center',
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: {
        color: '#a6a6a6',
        fontFamily: 'IBM Plex Mono, monospace',
        fontSize: 11,
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['52%', '74%'],
        center: ['50%', '43%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: '#0d0e10',
          borderWidth: 2,
        },
        label: {
          show: true,
          color: '#a6a6a6',
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 10.5,
          formatter: '{d}%',
        },
        labelLine: {
          length: 10,
          length2: 12,
          lineStyle: { color: '#525252' },
        },
        data: seriesData,
      },
    ],
  };
</script>

<div class="donut-wrap">
  <ECharts {data} {config} {height} />
</div>

<style>
  .donut-wrap {
    inline-size: 100%;
    min-inline-size: 0;
  }
</style>
