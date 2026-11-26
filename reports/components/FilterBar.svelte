<script>
  import { getInputContext } from '@evidence-dev/sdk/utils/svelte';

  export let defaults = {};
  export let label = 'Limpar filtros';

  const inputs = getInputContext();
  let resetKey = 0;

  function isInputObject(entry) {
    // Evidence's setTrackProxy wraps objects around a function (() => {}), so typeof can be 'function'
    return (
      entry !== null &&
      entry !== undefined &&
      (typeof entry === 'object' || typeof entry === 'function') &&
      'value' in entry
    );
  }

  function readValue(entry) {
    if (entry === null || entry === undefined) return '';
    if (isInputObject(entry)) {
      const v = entry.value;
      if (v === null || v === undefined) return '';
      return String(v);
    }
    return String(entry);
  }

  $: defaultEntries = Object.entries(defaults || {});

  $: isDirty = defaultEntries.some(([key, defVal]) => {
    if (!$inputs || !(key in $inputs)) return false;
    const val = readValue($inputs[key]);
    if (!val || val.includes('An Input has not been set')) return false;
    return val !== String(defVal);
  });

  function resetFilters() {
    if (!isDirty) return;
    // Mutate properties directly on the existing setTrackProxy store without spreading it
    for (const [key, defVal] of defaultEntries) {
      const current = $inputs[key];
      if (isInputObject(current)) {
        // Omit rawValues so remounted Dropdown sees ('rawValues' in $inputs[name] === false)
        // and re-initializes cleanly from defaultValue while keeping .value defined during remount
        $inputs[key] = { value: defVal, label: String(defVal) };
      } else {
        $inputs[key] = defVal;
      }
    }
    resetKey += 1;
  }
</script>

<div class="controls-left">
  {#key resetKey}
    <slot />
  {/key}

  <button
    type="button"
    class="filter-reset-btn"
    class:is-dirty={isDirty}
    disabled={!isDirty}
    aria-label="Restaurar filtros padrão"
    on:click={resetFilters}
  >
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5"
        stroke="currentColor"
        stroke-width="1.9"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    <span>{label}</span>
  </button>
</div>

<style>
  .filter-reset-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: max(34px, var(--target-size, 28px));
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #262626;
    background: #161616;
    color: #575757;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    line-height: 1;
    white-space: nowrap;
    cursor: default;
    transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }

  .filter-reset-btn.is-dirty {
    border-color: rgba(255, 107, 0, 0.55);
    background: #212121;
    color: #ff6b00;
    font-weight: 600;
    cursor: pointer;
  }

  .filter-reset-btn.is-dirty:hover {
    background: #2a190d;
    border-color: #ff6b00;
    color: #ff8533;
  }

  .filter-reset-btn:focus-visible {
    outline: 2px solid #ff6b00;
    outline-offset: 2px;
  }
</style>
