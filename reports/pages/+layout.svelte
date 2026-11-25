<script>
  import '@evidence-dev/tailwind/fonts.css';
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { base } from '$app/paths';
  import { EvidenceDefaultLayout } from '@evidence-dev/core-components';

  export let data;

  const navItems = [
    { label: 'Panorama', path: '/' },
    { label: 'Inteligência', path: '/inteligencia-de-mercado' },
    { label: 'Juros', path: '/juros-e-atividade' },
    { label: 'Inflação', path: '/inflacao-e-trabalho' },
    { label: 'Câmbio', path: '/cambio' },
    { label: 'Focus', path: '/focus' },
    { label: 'Linhagem', path: '/qualidade-e-linhagem' },
  ];

  let headerEl;
  let headerInnerEl;
  let menuEl;
  let isWide = false;
  let isMeasuring = false;
  let lastCollapsedWidth = 0;

  function normalizePath(pathname) {
    if (!pathname) return '/';
    let p = pathname;
    if (base && p.startsWith(base)) {
      p = p.slice(base.length) || '/';
    }
    if (p.length > 1 && p.endsWith('/')) {
      p = p.slice(0, -1);
    }
    return p || '/';
  }

  function isCurrent(itemPath, currentPathname) {
    return normalizePath(currentPathname) === itemPath;
  }

  function closeMobileMenu() {
    if (!menuEl || isWide) return;
    try {
      if (typeof menuEl.hidePopover === 'function' && menuEl.matches(':popover-open')) {
        menuEl.hidePopover();
      }
    } catch {
      menuEl.classList.remove(':popover-open');
    }
  }

  function syncNavLayout(force = false) {
    if (!headerEl || !headerInnerEl || !menuEl) return;

    const currentWidth = headerEl.clientWidth;
    if (!force && !isWide && currentWidth <= lastCollapsedWidth) {
      return;
    }

    let wasOpen = false;
    try {
      wasOpen = menuEl.matches(':popover-open');
    } catch {
      wasOpen = menuEl.classList.contains(':popover-open');
    }

    isMeasuring = true;
    headerEl.classList.add('is-measuring', 'is-wide');
    menuEl.removeAttribute('popover');

    const fits = headerInnerEl.scrollWidth <= headerInnerEl.clientWidth + 1;

    if (fits) {
      isWide = true;
      lastCollapsedWidth = 0;
    } else {
      isWide = false;
      lastCollapsedWidth = currentWidth;
      headerEl.classList.remove('is-wide');
      menuEl.setAttribute('popover', 'auto');
      if (wasOpen && typeof menuEl.showPopover === 'function') {
        try {
          menuEl.showPopover();
        } catch {
          // Ignore if browser rejects re-opening during resize
        }
      }
    }

    requestAnimationFrame(() => {
      isMeasuring = false;
      headerEl?.classList.remove('is-measuring');
    });
  }

  function handleFallbackToggle() {
    if (!menuEl || isWide) return;
    if (Object.hasOwn(HTMLElement.prototype, 'popover')) return;
    menuEl.classList.toggle(':popover-open');
  }

  onMount(() => {
    try {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('evidence-theme', 'dark');
    } catch {
      document.documentElement.setAttribute('data-theme', 'dark');
    }

    syncNavLayout(true);

    const observer = new ResizeObserver(() => {
      syncNavLayout(false);
    });
    if (headerEl) observer.observe(headerEl);
    if (menuEl) observer.observe(menuEl);

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => syncNavLayout(true));
    }

    return () => {
      observer.disconnect();
    };
  });

  $: if ($page.url.pathname) {
    closeMobileMenu();
  }
</script>

<svelte:head>
  <meta name="color-scheme" content="dark" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link
    href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<EvidenceDefaultLayout
  {data}
  title="BCB Macro"
  fullWidth={true}
  hideSidebar={true}
  hideHeader={true}
  hideBreadcrumbs={true}
  hideTOC={true}
  neverShowQueries={true}
  builtWithEvidence={false}
>
  <div slot="content" class="bcb-app-shell">
    <header
      bind:this={headerEl}
      class="site-header"
      class:is-wide={isWide}
      class:is-measuring={isMeasuring}
    >
      <div bind:this={headerInnerEl} class="header-inner">
        <a class="site-brand" href={`${base}/`}>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <rect x="3" y="13" width="4" height="7" rx="1" fill="#F5F5F5" />
            <rect x="10" y="8" width="4" height="12" rx="1" fill="#F5F5F5" />
            <rect x="17" y="4" width="4" height="16" rx="1" fill="#3B82F6" />
          </svg>
          <span>BCB Macro</span>
        </a>

        <nav class="site-nav" aria-label="Navegação principal">
          <button
            class="menu-button"
            type="button"
            popovertarget="bcb-site-menu"
            popovertargetaction="toggle"
            aria-controls="bcb-site-menu"
            on:click={handleFallbackToggle}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M4 7h16M4 12h16M4 17h16"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
              />
            </svg>
            <span>Menu</span>
          </button>

          <ul
            bind:this={menuEl}
            id="bcb-site-menu"
            class="site-menu"
            popover="auto"
          >
            {#each navItems as item}
              <li>
                <a
                  href={item.path === '/' ? `${base}/` : `${base}${item.path}`}
                  aria-current={isCurrent(item.path, $page.url.pathname) ? 'page' : undefined}
                  on:click={closeMobileMenu}
                >
                  {item.label}
                </a>
              </li>
            {/each}
          </ul>
        </nav>

        <a
          class="repo-link"
          href="https://github.com/leoserpa/bcb-dados-macro"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Abrir repositório no GitHub"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z" />
          </svg>
        </a>
      </div>
    </header>

    <div class="bcb-page-container">
      <slot />
    </div>
  </div>
</EvidenceDefaultLayout>

<style>
  :global(:root),
  :global(html[data-theme='dark']) {
    color-scheme: dark;
    accent-color: #3b82f6;
    --bcb-canvas: #0f0f0f;
    --bcb-surface: #161616;
    --bcb-elevated: #252525;
    --bcb-border: #282828;
    --bcb-divider: #202020;
    --bcb-text: #f5f5f5;
    --bcb-text-secondary: #a6a6a6;
    --bcb-text-muted: #737373;
    --bcb-text-dim: #575757;
    --bcb-accent: #3b82f6;
    --bcb-accent-soft: #60a5fa;
    --target-size: 28px;
    --scrollbar-track: #161616;
    --scrollbar-thumb: #525252;
    scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
  }

  @media (pointer: coarse) {
    :global(:root) {
      --target-size: 44px;
    }
  }

  @supports not (scrollbar-color: auto) {
    :global(html),
    :global(.bcb-table-scroll) {
      scrollbar-width: auto;
    }
    :global(html::-webkit-scrollbar),
    :global(.bcb-table-scroll::-webkit-scrollbar) {
      width: 10px;
      height: 10px;
    }
    :global(html::-webkit-scrollbar-thumb),
    :global(.bcb-table-scroll::-webkit-scrollbar-thumb) {
      background: var(--scrollbar-thumb);
      border-radius: 6px;
    }
    :global(html::-webkit-scrollbar-track),
    :global(.bcb-table-scroll::-webkit-scrollbar-track) {
      background: var(--scrollbar-track);
    }
  }

  :global(html) {
    scroll-padding-top: calc(4.25rem + env(safe-area-inset-top, 0px));
    background-color: #0f0f0f !important;
  }

  :global(html),
  :global(body) {
    background-color: #0f0f0f !important;
    color: #f5f5f5 !important;
    font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif !important;
    overflow-wrap: break-word;
  }

  :global(main),
  :global(#evidence-main-article),
  :global(.content-container) {
    background-color: #0f0f0f !important;
    max-width: 100% !important;
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  :global(#evidence-main-article h1.title) {
    display: none;
  }

  :global(h1),
  :global(h2),
  :global(h3) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    letter-spacing: -0.018em;
    color: #f5f5f5;
    text-wrap: balance;
  }

  :global(p),
  :global(li) {
    text-wrap: pretty;
  }

  :global(code),
  :global(pre),
  :global(table td),
  :global(table th),
  :global(.tabular-nums) {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  :global(a),
  :global(code) {
    overflow-wrap: anywhere;
  }

  /* ==================== SHELL & TOP NAVBAR ==================== */
  .bcb-app-shell {
    min-block-size: 100dvh;
    background: #0f0f0f;
    color: #f5f5f5;
  }

  .site-header {
    position: sticky;
    inset-block-start: 0;
    z-index: 40;
    background: rgba(15, 15, 15, 0.92);
    backdrop-filter: blur(8px);
    padding-block-start: max(0.65rem, env(safe-area-inset-top, 0px));
    padding-block-end: 0.65rem;
    padding-inline-start: max(clamp(16px, 4vw, 64px), env(safe-area-inset-left, 0px));
    padding-inline-end: max(clamp(16px, 4vw, 64px), env(safe-area-inset-right, 0px));
  }

  .header-inner {
    max-inline-size: 1280px;
    margin-inline: auto;
    display: flex;
    align-items: center;
    gap: 24px;
    min-block-size: 40px;
  }

  .header-inner > * {
    flex-shrink: 0;
    white-space: nowrap;
  }

  .site-brand {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #f5f5f5;
    text-decoration: none;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.02em;
    min-block-size: var(--target-size);
  }

  .site-brand:focus-visible,
  .menu-button:focus-visible,
  .repo-link:focus-visible,
  .site-menu a:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
    border-radius: 6px;
  }

  .site-nav {
    display: flex;
    align-items: center;
    margin-inline-start: auto;
  }

  .site-header.is-wide .site-nav {
    margin-inline-start: 0;
    margin-inline-end: auto;
  }

  .menu-button {
    anchor-name: --menu-button;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: var(--target-size);
    min-inline-size: var(--target-size);
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #282828;
    background: #161616;
    color: #f5f5f5;
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
  }

  .menu-button:hover {
    background: #252525;
  }

  .site-menu {
    position: fixed;
    inset: auto;
    inset-block-start: calc(3.75rem + env(safe-area-inset-top, 0px));
    inset-block-start: anchor(--menu-button bottom);
    inset-inline-end: max(1rem, env(safe-area-inset-right, 0px));
    inline-size: min(84dvw, 19rem);
    max-inline-size: calc(100dvw - 2rem);
    block-size: fit-content;
    max-block-size: calc(100dvh - 5.5rem);
    margin: 0.5rem 0 0;
    padding: 8px;
    list-style: none;
    overflow: auto;
    border-radius: 8px;
    border: 1px solid #282828;
    background: #161616;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
  }

  .site-menu::backdrop {
    background: rgba(0, 0, 0, 0.45);
  }

  @supports not selector(:popover-open) {
    .site-menu[popover]:not(.\:popover-open) {
      display: none;
    }
    .site-menu[popover].\:popover-open {
      display: block;
    }
  }

  .site-menu a {
    display: flex;
    align-items: center;
    min-block-size: max(38px, var(--target-size));
    padding: 6px 12px;
    border-radius: 6px;
    color: #a6a6a6;
    text-decoration: none;
    font-size: 13px;
    font-weight: 400;
    border-inline-start: 2px solid transparent;
  }

  .site-menu a:hover {
    background: #202020;
    color: #f5f5f5;
  }

  .site-menu a[aria-current='page'] {
    background: #252525;
    color: #f5f5f5;
    font-weight: 600;
    border-inline-start-color: #3b82f6;
  }

  .site-header.is-wide .menu-button {
    display: none;
  }

  .site-header.is-wide .site-menu {
    position: static;
    display: flex;
    align-items: center;
    gap: 4px;
    inline-size: auto;
    max-inline-size: none;
    block-size: auto;
    max-block-size: none;
    overflow: visible;
    margin: 0;
    padding: 0;
    border: 0;
    background: transparent;
    box-shadow: none;
  }

  .site-header.is-wide .site-menu::backdrop {
    display: none;
  }

  .site-header.is-wide .site-menu a {
    min-block-size: var(--target-size);
    padding: 5px 10px;
    font-size: 12px;
    color: #737373;
    border-inline-start: 0;
    border-block-end: 2px solid transparent;
    border-radius: 6px 6px 0 0;
  }

  .site-header.is-wide .site-menu a:hover {
    background: transparent;
    color: #f5f5f5;
  }

  .site-header.is-wide .site-menu a[aria-current='page'] {
    background: transparent;
    color: #f5f5f5;
    font-weight: 600;
    border-block-end-color: #3b82f6;
  }

  .site-header.is-measuring * {
    transition: none !important;
  }

  .repo-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-block-size: var(--target-size);
    min-inline-size: var(--target-size);
    color: #737373;
    text-decoration: none;
  }

  .repo-link:hover {
    color: #f5f5f5;
  }

  @media (forced-colors: active) {
    .site-menu a[aria-current='page'] {
      border-color: Highlight;
      text-decoration: underline;
    }
  }

  /* ==================== PAGE CONTAINER ==================== */
  .bcb-page-container {
    max-inline-size: 1280px;
    margin-inline: auto;
    padding-block-start: clamp(14px, 2vw, 24px);
    padding-block-end: max(40px, env(safe-area-inset-bottom, 0px));
    padding-inline-start: max(clamp(16px, 4vw, 64px), env(safe-area-inset-left, 0px));
    padding-inline-end: max(clamp(16px, 4vw, 64px), env(safe-area-inset-right, 0px));
  }

  /* ==================== PAGE HEADER & CONTROLS ==================== */
  :global(.page-hero) {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-block-end: 20px;
  }

  :global(.page-title-group) {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  :global(.page-title) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: clamp(20px, 2.2vw, 24px);
    font-weight: 700;
    color: #f5f5f5;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }

  :global(.page-subtitle) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 12.5px;
    color: #737373;
    margin: 0;
    line-height: 1.4;
  }

  :global(.controls-bar) {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 10px 14px;
  }

  :global(.controls-left),
  :global(.controls-right) {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 10px;
  }

  :global(.status-chip) {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-block-size: 32px;
    padding: 5px 12px;
    border-radius: 6px;
    background: #161616;
    border: 1px solid #282828;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 11px;
    font-weight: 500;
    color: #a6a6a6;
    white-space: nowrap;
  }

  :global(.status-chip-dot) {
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: #3b82f6;
    display: inline-block;
  }

  /* ==================== JOINED SEGMENTED BUTTON GROUP (POWER UI V4) ==================== */
  :global(.controls-bar [role='group']) {
    background: #161616 !important;
    border: 1px solid #282828 !important;
    border-radius: 6px !important;
    height: auto !important;
    min-block-size: max(32px, var(--target-size));
    box-shadow: none !important;
    margin-bottom: 0 !important;
  }

  :global(.controls-bar [role='group'] button) {
    min-block-size: max(32px, var(--target-size));
    padding: 6px 14px !important;
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    font-size: 11.5px !important;
    font-weight: 500 !important;
    border-color: #282828 !important;
    background-color: #161616 !important;
    color: #737373 !important;
    transition: background-color 0.15s ease, color 0.15s ease;
  }

  :global(.controls-bar [role='group'] button:hover) {
    background-color: #202020 !important;
    color: #f5f5f5 !important;
  }

  :global(.controls-bar [role='group'] button.text-primary),
  :global(.controls-bar [role='group'] button.bg-base-200) {
    background-color: #252525 !important;
    color: #f5f5f5 !important;
    font-weight: 600 !important;
  }

  :global(.controls-bar button[role='combobox']) {
    min-block-size: max(32px, var(--target-size));
    background-color: #161616 !important;
    border-color: #282828 !important;
    color: #f5f5f5 !important;
    font-size: 12px !important;
  }

  :global(.controls-bar .inline-block) {
    margin: 0 !important;
  }

  /* ==================== RESPONSIVE GRIDS ==================== */
  :global(.kpi-grid-5) {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
    margin-block-end: 18px;
  }

  :global(.kpi-grid-6) {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 12px;
    margin-block-end: 18px;
  }

  :global(.kpi-grid-4) {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-block-end: 18px;
  }

  :global(.terminal-grid-2) {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin-block-end: 18px;
  }

  :global(.terminal-grid-3) {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    margin-block-end: 18px;
  }

  :global(.terminal-grid-asym) {
    display: grid;
    grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
    gap: 16px;
    margin-block-end: 18px;
    align-items: start;
  }

  :global(.terminal-grid-asym-wide) {
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
    gap: 16px;
    margin-block-end: 18px;
    align-items: start;
  }

  :global(.terminal-stack) {
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-inline-size: 0;
  }

  /* ==================== PANELS & DATA-INK CHARTS ==================== */
  :global(.terminal-panel) {
    background: #161616;
    border: 1px solid #282828;
    border-radius: 8px;
    padding: 18px 20px;
    min-inline-size: 0;
    --base-100: #161616;
    --twc-base-100: 0 0% 8.6%;
  }

  :global(.terminal-panel .chart-container),
  :global(.terminal-panel .chart-container > div),
  :global(.terminal-panel .bg-base-100),
  :global(.terminal-panel canvas) {
    background-color: transparent !important;
  }

  :global(.panel-head) {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
    margin-block-end: 8px;
  }

  :global(.terminal-panel-title) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 13.5px;
    font-weight: 500;
    color: #f5f5f5;
    margin: 0 0 2px 0;
    line-height: 1.3;
  }

  :global(.terminal-panel-sub) {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    font-size: 11px;
    color: #737373;
    margin: 0 0 10px 0;
    line-height: 1.35;
  }

  /* ==================== TABLES (RESPONSIVE & TABULAR) ==================== */
  :global(.terminal-panel .table-container),
  :global(.terminal-panel .overflow-auto),
  :global(.terminal-panel .overflow-x-auto) {
    max-inline-size: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  :global(.terminal-panel table) {
    background: transparent !important;
    border-collapse: collapse;
    inline-size: 100%;
  }

  :global(.terminal-panel thead th) {
    position: sticky;
    inset-block-start: 0;
    background: #161616 !important;
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
    font-size: 10.5px !important;
    font-weight: 500 !important;
    color: #737373 !important;
    border-bottom: 1px solid #202020 !important;
    padding-block: 8px !important;
    white-space: nowrap;
  }

  :global(.terminal-panel tbody td) {
    font-size: 11.5px !important;
    color: #d4d4d4 !important;
    border-bottom: 1px solid #202020 !important;
    padding-block: 7px !important;
    white-space: nowrap;
  }

  :global(.terminal-panel tbody tr:last-child td) {
    border-bottom: 0 !important;
  }

  /* ==================== RESPONSIVE BREAKPOINTS (TABLET & MOBILE) ==================== */
  @media (max-width: 1180px) {
    :global(.kpi-grid-6) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    :global(.kpi-grid-5) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 1024px) {
    :global(.terminal-grid-3) {
      grid-template-columns: 1fr;
    }
    :global(.terminal-grid-asym),
    :global(.terminal-grid-asym-wide) {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 900px) {
    :global(.terminal-grid-2) {
      grid-template-columns: 1fr;
    }
    :global(.kpi-grid-4) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 640px) {
    :global(.kpi-grid-5),
    :global(.kpi-grid-6) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    :global(.terminal-panel) {
      padding: 14px 14px;
    }

    :global(.controls-bar) {
      flex-direction: column;
      align-items: stretch;
    }

    :global(.controls-left),
    :global(.controls-right) {
      inline-size: 100%;
    }
  }

  @media (max-width: 380px) {
    :global(.kpi-grid-4),
    :global(.kpi-grid-5),
    :global(.kpi-grid-6) {
      grid-template-columns: 1fr;
    }
  }
</style>
