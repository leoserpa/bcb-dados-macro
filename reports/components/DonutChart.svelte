<script>
  import { ECharts } from '@evidence-dev/core-components';

  export let data = [];
  export let nameCol = 'tabela';
  export let valueCol = 'registros';
  export let height = '230px';

  const palette = ['#3b82f6', '#2563eb', '#60a5fa', '#1e3a8a', '#525252'];

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
      backgroundColor: '#212121',
      borderColor: '#282828',
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
          borderColor: '#161616',
          borderWidth: 2,
        },
        label: {
          show: true,
          color: '#a6a6a6',
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: 10,
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
