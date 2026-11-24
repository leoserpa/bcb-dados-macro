<script>
  import '@evidence-dev/tailwind/fonts.css';
  import '../app.css';
  import { onMount } from 'svelte';
  import { EvidenceDefaultLayout } from '@evidence-dev/core-components';

  export let data;

  onMount(() => {
    try {
      const saved = localStorage.getItem('evidence-theme');
      if (!saved || saved === 'system') {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('evidence-theme', 'dark');
      }
    } catch {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  });
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link
    href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<EvidenceDefaultLayout
  {data}
  title="BCB MACRO"
  fullWidth={true}
  hideTOC={true}
  hideBreadcrumbs={true}
  neverShowQueries={true}
  githubRepo="https://github.com/leoserpa/bcb-dados-macro"
>
  <slot slot="content" />
</EvidenceDefaultLayout>

<style>
  :global(:root),
  :global(html[data-theme='dark']) {
    --bcb-canvas: #0f0f0f;
    --bcb-surface: #161616;
    --bcb-elevated: #212121;
    --bcb-border: #2a2a2a;
    --bcb-text: #f5f5f5;
    --bcb-text-secondary: #a3a3a3;
    --bcb-text-muted: #737373;
    --bcb-accent: #3b82f6;
  }

  :global(html:not([data-theme='light'])),
  :global(html:not([data-theme='light']) body) {
    background-color: #0f0f0f !important;
    color: #f5f5f5 !important;
    font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif !important;
  }

  :global(html:not([data-theme='light']) header) {
    background-color: rgba(15, 15, 15, 0.92) !important;
    border-bottom: 1px solid #2a2a2a !important;
  }

  :global(html:not([data-theme='light']) aside),
  :global(html:not([data-theme='light']) nav) {
    background-color: #161616 !important;
    border-color: #2a2a2a !important;
  }

  :global(html:not([data-theme='light']) main),
  :global(html:not([data-theme='light']) #evidence-main-article) {
    background-color: #0f0f0f !important;
    max-width: 100% !important;
  }

  :global(#evidence-main-article h1.title) {
    display: none;
  }

  :global(h1),
  :global(h2),
  :global(h3) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    letter-spacing: -0.015em;
    color: #f5f5f5;
  }

  :global(code),
  :global(pre),
  :global(table td),
  :global(table th),
  :global(.tabular-nums) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  :global(.terminal-header) {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid #2a2a2a;
  }

  :global(.terminal-title) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #f5f5f5;
    margin: 0 0 4px 0;
    line-height: 1.25;
  }

  :global(.terminal-subtitle) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #a3a3a3;
    margin: 0;
  }

  :global(.status-pills) {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }

  :global(.status-pill) {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 6px;
    background: #161616;
    border: 1px solid #2a2a2a;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    font-weight: 500;
    color: #f5f5f5;
  }

  :global(.status-dot) {
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: #3b82f6;
    display: inline-block;
  }

  :global(.filter-bar) {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    padding: 10px 14px;
    margin: 0 0 18px;
    border-radius: 8px;
    border: 1px solid #2a2a2a;
    background: #161616;
  }

  :global(.filter-bar button[role='combobox']) {
    background-color: #212121 !important;
    border-color: #2a2a2a !important;
    color: #f5f5f5 !important;
  }

  :global(.section-kicker) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #737373;
    margin: 16px 0 10px;
  }

  :global(.kpi-grid-5) {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
    margin: 0 0 20px;
  }

  :global(.kpi-grid-6) {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 12px;
    margin: 0 0 20px;
  }

  :global(.terminal-grid-2) {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin: 0 0 18px;
  }

  :global(.terminal-panel) {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 18px 20px;
    min-width: 0;
  }

  :global(.terminal-panel-title) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #f5f5f5;
    margin: 0 0 2px 0;
  }

  :global(.terminal-panel-sub) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    color: #737373;
    margin: 0 0 12px 0;
  }

  :global(.terminal-panel table) {
    background: transparent !important;
  }

  :global(.terminal-panel th) {
    font-size: 10px !important;
    text-transform: uppercase;
    color: #737373 !important;
    border-color: #2a2a2a !important;
  }

  :global(.terminal-panel td) {
    font-size: 12px !important;
    border-color: #262626 !important;
  }

  @media (max-width: 1280px) {
    :global(.kpi-grid-5),
    :global(.kpi-grid-6) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 900px) {
    :global(.terminal-grid-2) {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 680px) {
    :global(.kpi-grid-5),
    :global(.kpi-grid-6) {
      grid-template-columns: 1fr;
    }
  }
</style>
