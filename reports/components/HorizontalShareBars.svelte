<script>
  export let data = [];
  export let nameCol = 'fonte';
  export let valueCol = 'registros';

  $: rows = Array.isArray(data)
    ? data
    : data && typeof data[Symbol.iterator] === 'function'
      ? Array.from(data)
      : [];

  $: total = rows.reduce((sum, r) => sum + (Number(r[valueCol]) || 0), 0);
  $: maxVal = rows.reduce((m, r) => Math.max(m, Number(r[valueCol]) || 0), 0);

  $: items = rows.map((r, idx) => {
    const val = Number(r[valueCol]) || 0;
    const pct = total > 0 ? (val / total) * 100 : 0;
    const widthPct = maxVal > 0 ? Math.max(4, (val / maxVal) * 100) : 0;
    return {
      name: String(r[nameCol] ?? ''),
      value: val,
      pct,
      widthPct,
      isLeader: idx === 0,
    };
  });
</script>

<div class="hbar-list" role="list" aria-label="Distribuição de registros por fonte oficial">
  {#each items as item}
    <div class="hbar-item" role="listitem">
      <div class="hbar-meta">
        <span class="hbar-name" class:is-leader={item.isLeader}>{item.name}</span>
        <span class="hbar-count">{item.value.toLocaleString('pt-BR')} reg.</span>
      </div>

      <div class="hbar-track-row">
        <div class="hbar-bar-area">
          <div
            class="hbar-fill"
            class:is-leader={item.isLeader}
            style={`width: ${item.widthPct.toFixed(1)}%;`}
          ></div>
          <span class="hbar-pct" class:is-leader={item.isLeader}>
            {item.pct.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
          </span>
        </div>
      </div>
    </div>
  {/each}

  {#if total > 0}
    <div class="hbar-foot">
      <span>Total consolidado Silver</span>
      <span class="hbar-total">{total.toLocaleString('pt-BR')} registros</span>
    </div>
  {/if}
</div>

<style>
  .hbar-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-block-start: 4px;
    inline-size: 100%;
    min-inline-size: 0;
  }

  .hbar-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-inline-size: 0;
  }

  .hbar-meta {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    min-inline-size: 0;
  }

  .hbar-name {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12.5px;
    font-weight: 500;
    color: #a6a6a6;
    line-height: 1.25;
  }

  .hbar-name.is-leader {
    color: #f5f5f5;
    font-weight: 600;
  }

  .hbar-count {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #737373;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .hbar-track-row {
    inline-size: 100%;
    padding-inline-end: 54px;
    box-sizing: border-box;
  }

  .hbar-bar-area {
    display: flex;
    align-items: center;
    gap: 10px;
    inline-size: 100%;
  }

  .hbar-fill {
    block-size: 16px;
    border-radius: 3px;
    background: #525252;
    flex-shrink: 0;
    transition: width 0.25s ease;
  }

  .hbar-fill.is-leader {
    background: #ff6b00;
  }

  .hbar-pct {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 12px;
    font-weight: 600;
    color: #a6a6a6;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .hbar-pct.is-leader {
    color: #ff6b00;
  }

  .hbar-foot {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    padding-block-start: 10px;
    margin-block-start: 2px;
    border-block-start: 1px solid #202020;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #737373;
  }

  .hbar-total {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11.5px;
    font-weight: 600;
    color: #d4d4d4;
    font-variant-numeric: tabular-nums;
  }
</style>
