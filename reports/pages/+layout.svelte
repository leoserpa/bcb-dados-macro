<script>
  import '@evidence-dev/tailwind/fonts.css';
  import '../app.css';
  import { EvidenceDefaultLayout } from '@evidence-dev/core-components';

  export let data;
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
  githubRepo="https://github.com/leoserpa/bcb-dados-macro"
>
  <slot slot="content" />
</EvidenceDefaultLayout>

<style>
  :global(:root) {
    --bcb-canvas: #0f0f0f;
    --bcb-surface: #161616;
    --bcb-elevated: #212121;
    --bcb-border: #2a2a2a;
    --bcb-text: #f5f5f5;
    --bcb-text-secondary: #a3a3a3;
    --bcb-text-muted: #737373;
    --bcb-accent: #3b82f6;
  }

  :global(html.dark),
  :global(html.dark body),
  :global(html[data-theme='dark']),
  :global(html[data-theme='dark'] body) {
    background-color: var(--bcb-canvas) !important;
    color: var(--bcb-text) !important;
    font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif !important;
  }

  :global(html.dark main),
  :global(html.dark header),
  :global(html.dark aside) {
    background-color: var(--bcb-canvas);
  }

  :global(html.dark aside) {
    background-color: var(--bcb-surface) !important;
    border-color: var(--bcb-border) !important;
  }

  :global(html.dark header) {
    border-color: var(--bcb-border) !important;
  }

  :global(h1),
  :global(h2),
  :global(h3) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    letter-spacing: -0.015em;
  }

  :global(code),
  :global(pre),
  :global(table td),
  :global(.tabular-nums) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  :global(.kpi-grid-5) {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
    margin: 14px 0 20px;
  }

  :global(.kpi-grid-6) {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 12px;
    margin: 14px 0 20px;
  }

  @media (max-width: 1200px) {
    :global(.kpi-grid-5),
    :global(.kpi-grid-6) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 720px) {
    :global(.kpi-grid-5),
    :global(.kpi-grid-6) {
      grid-template-columns: repeat(1, minmax(0, 1fr));
    }
  }

  :global(.filter-bar) {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: flex-end;
    padding: 12px 14px;
    margin: 12px 0 18px;
    border-radius: 8px;
    border: 1px solid #2a2a2a;
    background: #161616;
  }

  :global(.section-kicker) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #737373;
    margin: 18px 0 8px;
  }
</style>
