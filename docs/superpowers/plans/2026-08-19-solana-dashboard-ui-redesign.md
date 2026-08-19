# Solana Dashboard UI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete visual overhaul of the Solana Ecosystem Dashboard — new color system, typography, components, motion, responsive design, and accessibility.

**Architecture:** Single-page static dashboard (HTML + CSS + vanilla JS). CSS-first approach with design tokens, component-scoped styles, responsive grid system, and motion layer. JS enhanced for stagger animations, mobile nav, scroll detection, and a11y.

**Tech Stack:** HTML5, CSS3 (custom properties, Grid, Flexbox, @keyframes), Vanilla JS, Chart.js 4.x (CDN), Google Fonts (Inter + JetBrains Mono)

**Spec:** `docs/superpowers/specs/2026-08-19-solana-dashboard-ui-redesign.md`

## Global Constraints

- Zero external dependencies beyond Chart.js CDN and Google Fonts
- No build tools, no bundler, no npm
- All animations respect `prefers-reduced-motion`
- WCAG AA contrast ratios (4.5:1 normal text, 3:1 large text)
- Files: `dashboard/styles.css`, `dashboard/index.html`, `dashboard/app.js`
- Existing data files (`report.json`, `report.md`, `assets/`) unchanged

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `dashboard/styles.css` | **Rewrite** | All design tokens, layout, components, responsive, motion, a11y |
| `dashboard/index.html` | **Rewrite** | Semantic landmarks, a11y attributes, mobile nav markup, restructured sections |
| `dashboard/app.js` | **Modify** | Stagger animations, mobile nav toggle, scroll-based topbar blur, a11y JS |

---

## Task 1: CSS Design Tokens & Foundation

**Files:**
- Modify: `dashboard/styles.css` (replace entire file)

**Interfaces:**
- Consumes: None (foundation layer)
- Produces: CSS custom properties used by all subsequent tasks

- [ ] **Step 1: Write CSS custom properties and reset**

Replace the entire `styles.css` with the new design token system:

```css
/* Solana Ecosystem Intelligence — Design System v3.0 */
:root {
  /* Surfaces */
  --bg: #06080C;
  --surface: #0C1017;
  --surface-2: #111720;
  --surface-3: #18202C;
  --surface-4: #1E2636;
  --border: rgba(255,255,255,0.06);
  --border-strong: rgba(255,255,255,0.14);
  --border-glow: rgba(153,69,255,0.3);

  /* Brand */
  --accent: #9945FF;
  --teal: #14F195;
  --accent-grad: linear-gradient(135deg, #9945FF 0%, #14F195 100%);
  --accent-soft: rgba(153,69,255,0.14);
  --teal-soft: rgba(20,241,149,0.14);

  /* Semantic */
  --up: #2FE6A2;
  --up-soft: rgba(47,230,162,0.13);
  --down: #FF5C7A;
  --down-soft: rgba(255,92,122,0.13);
  --warn: #FFB224;
  --warn-soft: rgba(255,178,36,0.14);
  --danger: #FF4D5C;
  --danger-soft: rgba(255,77,92,0.14);

  /* Text */
  --text: #ECEEF4;
  --text-2: #9AA4B6;
  --text-3: #67728A;
  --text-dim: #49546A;

  /* Radii */
  --radius-lg: 16px;
  --radius-md: 12px;
  --radius-sm: 8px;
  --radius-pill: 999px;

  /* Shadows */
  --shadow-rest: 0 1px 0 rgba(255,255,255,0.02) inset, 0 4px 16px -8px rgba(0,0,0,0.5);
  --shadow-hover: 0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 32px -8px rgba(0,0,0,0.7);
  --shadow-cta: 0 6px 20px -8px rgba(153,69,255,0.6);

  /* Type */
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --mono: 'JetBrains Mono', 'SF Mono', monospace;
}

*, *::before, *::after { box-sizing: border-box; }
* { margin: 0; padding: 0; }
html { scroll-behavior: smooth; color-scheme: dark; }
body {
  font-family: var(--font);
  background:
    radial-gradient(1200px 500px at 80% -10%, rgba(153,69,255,0.08), transparent 60%),
    radial-gradient(900px 420px at 0% 0%, rgba(20,241,149,0.05), transparent 55%),
    var(--bg);
  color: var(--text);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
::selection { background: rgba(153,69,255,0.35); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 8px; border: 2px solid var(--bg); }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
```

- [ ] **Step 2: Verify in browser**

Open `dashboard/index.html` in browser. Background should be near-black (#06080C), text should be off-white (#ECEEF4). Scrollbar should be styled.

- [ ] **Step 3: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): design tokens and foundation reset"
```

---

## Task 2: CSS Layout System — App Shell & Topbar

**Files:**
- Modify: `dashboard/styles.css` (append after foundation)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Layout classes used by HTML sections

- [ ] **Step 1: Add app shell and topbar styles**

Append to `styles.css`:

```css
/* ============ App Shell ============ */
.app-shell { max-width: 1380px; margin: 0 auto; padding: 0 28px; }

/* ============ Topbar ============ */
.topbar {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 18px 0; margin-bottom: 34px;
  background: linear-gradient(var(--bg) 70%, rgba(6,8,12,0));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: backdrop-filter 0.3s ease;
}
.topbar.scrolled { backdrop-filter: blur(16px); background: rgba(6,8,12,0.92); }

.brand { display: flex; align-items: center; gap: 12px; }
.brand-logo { width: 34px; height: 34px; }
.brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.brand-title { font-weight: 700; font-size: 15px; letter-spacing: -0.01em; }
.brand-sub { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .08em; }

.topnav { display: flex; gap: 4px; background: var(--surface); border: 1px solid var(--border); padding: 4px; border-radius: var(--radius-pill); }
.topnav-link {
  color: var(--text-3); text-decoration: none; font-size: 13px; font-weight: 500;
  padding: 7px 16px; border-radius: var(--radius-pill); transition: all .18s ease;
}
.topnav-link:hover { color: var(--text); }
.topnav-link.active { background: var(--surface-3); color: var(--text); }

.topbar-actions { display: flex; align-items: center; gap: 10px; }

.health-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 12px; border-radius: var(--radius-pill);
  background: var(--teal-soft); color: var(--teal); font-size: 12.5px; font-weight: 600;
}
.health-pill.warn { background: var(--warn-soft); color: var(--warn); }
.health-pill.bad { background: var(--danger-soft); color: var(--danger); }

.dot { width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }
.dot-ok {
  background: var(--teal);
  box-shadow: 0 0 0 4px rgba(20,241,149,0.15);
  animation: pulse 2s infinite;
}
.dot-warn { background: var(--warn); box-shadow: 0 0 0 4px rgba(255,178,36,0.15); }
.dot-bad { background: var(--danger); box-shadow: 0 0 0 4px rgba(255,77,92,0.15); }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(20,241,149,0.12), 0 0 8px rgba(20,241,149,0.5); }
  50% { box-shadow: 0 0 0 7px rgba(20,241,149,0), 0 0 14px rgba(20,241,149,0.4); }
}

.updated-at { color: var(--text-3); font-size: 12.5px; font-family: var(--mono); white-space: nowrap; }

/* ============ Buttons ============ */
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  font-family: var(--font); font-size: 13px; font-weight: 600;
  padding: 9px 15px; border-radius: var(--radius-sm); cursor: pointer;
  border: 1px solid transparent; transition: all .18s ease; white-space: nowrap;
}
.btn-primary {
  background: var(--accent-grad); color: #0a0710;
  box-shadow: var(--shadow-cta);
}
.btn-primary:hover { filter: brightness(1.1); transform: translateY(-1px); }
.btn-primary:active { transform: none; }
.btn-ghost { background: var(--surface-2); color: var(--text-2); border-color: var(--border-strong); }
.btn-ghost:hover { color: var(--text); border-color: rgba(255,255,255,0.28); }
.btn-sm { padding: 6px 10px; font-size: 12px; }
```

- [ ] **Step 2: Verify in browser**

Topbar should be sticky, backdrop-blur visible when scrolling. Health pill with animated green dot. Buttons styled with hover effects.

- [ ] **Step 3: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): app shell, topbar, and button system"
```

---

## Task 3: CSS Sections, Hero, KPI Grid

**Files:**
- Modify: `dashboard/styles.css` (append)

**Interfaces:**
- Consumes: Design tokens and layout from Tasks 1-2
- Produces: Section, hero, and KPI card styles

- [ ] **Step 1: Add section, hero, and KPI styles**

Append to `styles.css`:

```css
/* ============ Sections ============ */
.section { margin-bottom: 54px; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 22px; flex-wrap: wrap; }
.section-head h2 { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; margin-top: 6px; }
.section-note { color: var(--text-3); font-size: 13px; }
.eyebrow { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .14em; color: var(--accent); }

/* ============ Hero ============ */
.hero { padding-top: 14px; }
.hero-layout {
  display: flex; align-items: center; justify-content: space-between; gap: 34px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg);
  padding: 36px 40px; box-shadow: var(--shadow-rest); flex-wrap: wrap;
}
.hero-copy { max-width: 680px; }
.hero h1 {
  font-size: clamp(36px, 5vw, 56px); font-weight: 800; letter-spacing: -0.04em;
  line-height: 1.1; margin: 12px 0 14px;
}
.hero-sub { color: var(--text-2); font-size: 16px; max-width: 600px; line-height: 1.6; }
.hero-meta { display: flex; gap: 10px; margin-top: 22px; flex-wrap: wrap; }
.meta-chip {
  font-family: var(--mono); font-size: 12px; color: var(--text-2);
  background: var(--surface-2); border: 1px solid var(--border);
  padding: 7px 13px; border-radius: var(--radius-pill);
}
.hero-status-card {
  display: flex; align-items: center; gap: 18px;
  background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 20px 24px; min-width: 260px;
}
.status-orb { width: 48px; height: 48px; border-radius: 50%; background: var(--teal-soft); display: flex; align-items: center; justify-content: center; }
.status-orb.warn { background: var(--warn-soft); }
.status-orb.bad { background: var(--danger-soft); }
.status-copy { display: flex; flex-direction: column; }
.status-label { font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: var(--text-3); }
.status-value { font-size: 22px; font-weight: 800; margin-top: 2px; }
.status-detail { font-size: 12.5px; color: var(--text-2); margin-top: 2px; }

/* ============ KPI Grid ============ */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.kpi-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 22px 24px; box-shadow: var(--shadow-rest);
  display: flex; flex-direction: column; gap: 10px;
  transition: transform .2s ease-out, border-color .2s ease, box-shadow .2s ease;
  position: relative; overflow: hidden;
}
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 24px; right: 24px; height: 2px;
  background: var(--accent-grad); opacity: 0; transition: opacity .2s ease; border-radius: 2px;
}
.kpi-card:hover {
  transform: translateY(-3px); border-color: var(--border-strong);
  box-shadow: var(--shadow-hover);
}
.kpi-card:hover::before { opacity: 1; }
.kpi-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--text-2); }
.kpi-value { font-size: 36px; font-weight: 800; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; line-height: 1.1; }
.kpi-delta { font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.delta-up { color: var(--up); }
.delta-down { color: var(--down); }
.kpi-sub { font-size: 12px; color: var(--text-3); }
.kpi-spark { margin-top: auto; height: 34px; }
```

- [ ] **Step 2: Verify in browser**

Hero section with large headline, KPI grid 4-column with hover lift effect and gradient top-line on hover.

- [ ] **Step 3: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): hero section and KPI card grid"
```

---

## Task 4: CSS Cards, Charts, Economy, Epoch Panel

**Files:**
- Modify: `dashboard/styles.css` (append)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Card, chart, economy, and epoch panel styles

- [ ] **Step 1: Add card, chart, economy, and epoch styles**

Append to `styles.css`:

```css
/* ============ Cards ============ */
.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  box-shadow: var(--shadow-rest);
}
.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.card-title { font-size: 14px; font-weight: 600; }
.chip {
  font-size: 11px; font-weight: 700; font-family: var(--mono);
  padding: 3px 10px; border-radius: var(--radius-pill);
}
.chip-accent { background: var(--accent-soft); color: var(--accent); }
.chip-up { background: var(--up-soft); color: var(--up); }
.chip-neutral { background: var(--surface-3); color: var(--text-2); }
.chip-ok { background: var(--teal-soft); color: var(--teal); }
.chip-warn { background: var(--warn-soft); color: var(--warn); }
.chip-bad { background: var(--danger-soft); color: var(--danger); }

/* ============ Epoch / Network Panel ============ */
.epoch-panel { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; }
.epoch-card, .network-card { padding: 26px 28px; }
.progress-track { height: 12px; background: var(--surface-3); border-radius: 8px; overflow: hidden; margin: 22px 0; }
.progress-fill {
  height: 100%; background: var(--accent-grad); border-radius: 8px;
  transition: width 1s cubic-bezier(.2,.8,.2,1);
  position: relative;
}
.progress-fill::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  animation: shimmer 3s infinite;
}
@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
.epoch-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px 28px; }
.epoch-stat { display: flex; flex-direction: column; }
.epoch-stat span { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .07em; }
.epoch-stat strong { font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; margin-top: 3px; }
.big-number { font-size: 52px; font-weight: 800; letter-spacing: -0.03em; margin: 18px 0 22px; font-variant-numeric: tabular-nums; }
.stat-rows { display: flex; flex-direction: column; gap: 12px; }
.stat-row { display: flex; justify-content: space-between; align-items: baseline; font-size: 13px; }
.stat-row span { color: var(--text-2); }
.stat-row strong { font-variant-numeric: tabular-nums; font-weight: 600; }

/* ============ Charts ============ */
.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.chart-card { padding: 22px 24px; }
.chart-wrap { position: relative; height: 220px; margin-top: 14px; }
.chart-wrap canvas { width: 100% !important; height: 100% !important; }

/* ============ Economy ============ */
.economy-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.econ-card { padding: 22px 24px; }
.econ-grid-inner { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 18px; margin: 16px 0 14px; }
.econ-item { display: flex; flex-direction: column; }
.econ-label { font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: .06em; }
.econ-item strong { font-size: 18px; font-weight: 700; margin-top: 3px; font-variant-numeric: tabular-nums; }
.mini-progress { display: flex; align-items: center; gap: 10px; }
.mini-progress-track { flex: 1; height: 6px; background: var(--surface-3); border-radius: 4px; overflow: hidden; }
.mini-progress-fill { height: 100%; background: var(--accent-grad); border-radius: 4px; }
.mini-progress-label { font-size: 11px; color: var(--text-3); font-family: var(--mono); }
.econ-caption { font-size: 11px; color: var(--text-3); margin-top: 8px; }
.econ-rev-note { font-size: 11px; color: var(--text-3); margin-top: 8px; line-height: 1.4; }
```

- [ ] **Step 2: Verify in browser**

Epoch progress bar with shimmer animation. Charts in 2-column grid. Economy cards in 4-column grid.

- [ ] **Step 3: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): cards, charts, economy, and epoch panel"
```

---

## Task 5: CSS Validators Table

**Files:**
- Modify: `dashboard/styles.css` (append)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Table styles with zebra striping, sticky header, hover effects

- [ ] **Step 1: Add validator table styles**

Append to `styles.css`:

```css
/* ============ Validators Table ============ */
.table-tools { display: flex; gap: 10px; align-items: center; }
.input {
  font-family: var(--font); font-size: 13px; padding: 9px 14px;
  background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm);
  color: var(--text); outline: none; transition: border-color .18s ease;
}
.input:focus { border-color: var(--accent); }
.input.search { width: 220px; }
.input.select {
  cursor: pointer; padding-right: 30px; appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' width='14' height='14' fill='none' stroke='%239AA4B6' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center;
}
.sort-hint { color: var(--text-3); font-size: 12px; margin-bottom: 10px; }
.table-wrap { overflow-x: auto; padding: 0; }
.table { width: 100%; border-collapse: collapse; font-size: 13px; }
.table thead {
  background: var(--surface-2); position: sticky; top: 0; z-index: 2;
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
}
.table th {
  padding: 12px 16px; text-align: left; font-weight: 600; font-size: 12px;
  color: var(--text-2); white-space: nowrap; user-select: none;
}
.table th.sortable { cursor: pointer; }
.table th.sortable:hover { color: var(--text); }
.table th.num { text-align: right; }
.table th .sort-icon { display: inline-block; width: 12px; margin-left: 4px; }
.table th.asc .sort-icon::after { content: '↑'; }
.table th.desc .sort-icon::after { content: '↓'; }
.table td {
  padding: 13px 16px; border-top: 1px solid var(--border); vertical-align: middle;
  transition: background .15s ease, border-color .15s ease;
}
.table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.table tbody tr { border-left: 3px solid transparent; }
.table tbody tr:nth-child(even) { background: rgba(255,255,255,0.015); }
.table tbody tr:hover { background: var(--surface-2); border-left-color: var(--accent); }
.table tbody tr:first-child td { border-top: none; }
.table-footer { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-top: 1px solid var(--border); }
.table-count { font-size: 12px; color: var(--text-3); }
.table-pager { display: flex; align-items: center; gap: 8px; }
.page-info { font-size: 12px; color: var(--text-2); font-family: var(--mono); }
.val-name { font-weight: 600; }
.val-pubkey { font-family: var(--mono); font-size: 11px; color: var(--text-3); }
.val-status {
  display: inline-flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 600;
  padding: 3px 10px; border-radius: var(--radius-pill);
}
.val-status.active { background: var(--teal-soft); color: var(--teal); }
.val-status.delinquent {
  background: var(--warn-soft); color: var(--warn);
  animation: delinq-pulse 2s infinite;
}
@keyframes delinq-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

- [ ] **Step 2: Verify in browser**

Table with zebra rows, sticky header with blur, row hover with left accent border, delinquent status pulsing.

- [ ] **Step 3: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): validator table with zebra, sticky header, hover"
```

---

## Task 6: CSS Roadmap, News, Anomalies, Footer

**Files:**
- Modify: `dashboard/styles.css` (append)

**Interfaces:**
- Consumes: Design tokens from Task 1
- Produces: Roadmap, news, anomaly, and footer styles

- [ ] **Step 1: Add roadmap, news, anomaly, and footer styles**

Append to `styles.css`:

```css
/* ============ Roadmap ============ */
.roadmap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; }
.roadmap-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 22px; box-shadow: var(--shadow-rest);
  display: flex; flex-direction: column; gap: 10px;
  transition: transform .2s ease-out, box-shadow .2s ease;
  border-left: 3px solid var(--accent);
}
.roadmap-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
.roadmap-card.critical { border-left-color: var(--danger); }
.roadmap-card.high { border-left-color: var(--warn); }
.roadmap-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.roadmap-cat { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--text-3); }
.roadmap-impact {
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
  padding: 3px 8px; border-radius: var(--radius-pill);
}
.impact-critical { background: var(--danger-soft); color: var(--danger); }
.impact-high { background: var(--warn-soft); color: var(--warn); }
.roadmap-title { font-size: 15px; font-weight: 600; }
.roadmap-desc { font-size: 12.5px; color: var(--text-2); line-height: 1.5; }
.roadmap-bottom { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: auto; }
.roadmap-status { font-size: 11px; font-weight: 600; color: var(--teal); }
.roadmap-docs { font-size: 11px; color: var(--accent); text-decoration: none; }
.roadmap-docs:hover { text-decoration: underline; }

/* ============ News ============ */
.news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 18px; }
.news-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 22px; box-shadow: var(--shadow-rest);
  display: flex; flex-direction: column; gap: 10px;
  transition: border-color .18s ease;
}
.news-card:hover { border-color: var(--border-strong); }
.news-tag {
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
  padding: 3px 9px; border-radius: var(--radius-pill); background: var(--accent-soft); color: var(--accent);
  align-self: flex-start;
}
.news-title { font-size: 15px; font-weight: 600; }
.news-summary { font-size: 12.5px; color: var(--text-2); line-height: 1.5; }
.news-date { font-size: 11px; color: var(--text-3); margin-top: auto; }

/* ============ Anomalies ============ */
.anomalies-card { padding: 26px 28px; }
.anomaly-body { margin-top: 12px; }
.anomaly-body .all-clear { color: var(--text-2); font-size: 14px; padding: 8px 0; }
.anomaly-list { display: flex; flex-direction: column; gap: 10px; }
.anomaly-item {
  display: flex; align-items: center; gap: 12px;
  background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 12px 16px;
}
.anomaly-icon { font-size: 18px; }
.anomaly-text { flex: 1; }
.anomaly-text strong { font-size: 13px; }
.anomaly-text p { font-size: 12px; color: var(--text-2); margin-top: 2px; }

/* ============ Footer ============ */
.footer {
  border-top: 1px solid var(--border); padding-top: 28px; margin-top: 24px; padding-bottom: 32px;
  font-size: 12.5px; color: var(--text-3);
}
.footer-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.footer-brand { display: flex; align-items: center; gap: 10px; }
.footer-logo { width: 22px; height: 22px; }
.footer-version { font-family: var(--mono); font-size: 11px; }
.footer-sources { margin-bottom: 14px; }
.footer-label { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--text-dim); margin-bottom: 6px; display: inline-block; }
.sources-list { display: flex; flex-wrap: wrap; gap: 8px; }
.source-chip { background: var(--surface-2); border: 1px solid var(--border); padding: 4px 10px; border-radius: var(--radius-sm); font-size: 11px; font-family: var(--mono); color: var(--text-2); }
.footer-note { font-size: 11px; color: var(--text-dim); margin-bottom: 8px; }
.footer-copy { font-size: 11px; color: var(--text-dim); }
```

- [ ] **Step 2: Verify in browser**

Roadmap cards with colored left borders. News cards with hover border glow. Anomaly panel. Footer with source chips.

- [ ] **Step 3: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): roadmap, news, anomalies, and footer"
```

---

## Task 7: CSS Loading, Toast, Responsive, Reduced Motion

**Files:**
- Modify: `dashboard/styles.css` (append)

**Interfaces:**
- Consumes: All design tokens and component styles from Tasks 1-6
- Produces: Loading overlay, toast, responsive breakpoints, reduced motion

- [ ] **Step 1: Add loading overlay and toast styles**

Append to `styles.css`:

```css
/* ============ Loading ============ */
.loading-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: var(--bg);
  display: flex; align-items: center; justify-content: center;
  transition: opacity .35s ease, visibility .35s ease;
}
.loading-overlay.hidden { opacity: 0; visibility: hidden; pointer-events: none; }
.loader-card {
  display: flex; flex-direction: column; align-items: center; gap: 18px;
  padding: 34px 44px; border-radius: var(--radius-lg);
  background: var(--surface); border: 1px solid var(--border); box-shadow: var(--shadow-rest);
}
.loader-logo { width: 46px; height: 46px; filter: drop-shadow(0 0 18px rgba(153,69,255,.5)); }
.loader-track { width: 190px; height: 3px; background: var(--surface-3); border-radius: 8px; overflow: hidden; }
.loader-fill { height: 100%; width: 40%; background: var(--accent-grad); border-radius: 8px; animation: load 1.1s ease-in-out infinite; }
@keyframes load { 0% { transform: translateX(-110%); } 100% { transform: translateX(320%); } }
.loader-label { font-size: 11px; letter-spacing: .06em; text-transform: uppercase; color: var(--text-3); }

/* ============ Toast ============ */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px; }
.toast {
  display: flex; align-items: center; gap: 10px;
  background: var(--surface-2); border: 1px solid var(--border-strong);
  padding: 12px 16px; border-radius: var(--radius-md); font-size: 13px;
  box-shadow: 0 12px 32px -12px rgba(0,0,0,.7); backdrop-filter: blur(8px);
  animation: slidein .25s ease;
}
.toast.leaving { opacity: 0; transform: translateY(8px); transition: all .25s ease; }
.toast .t-ic { color: var(--teal); font-weight: 700; }
@keyframes slidein { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
```

- [ ] **Step 2: Add responsive breakpoints**

Append to `styles.css`:

```css
/* ============ Responsive ============ */
@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .economy-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .app-shell { padding: 0 16px; }
  .topbar { flex-wrap: wrap; gap: 14px; margin-bottom: 24px; }
  .topnav { display: none; }
  .topnav.open {
    display: flex; position: fixed; inset: 0; z-index: 200;
    flex-direction: column; align-items: center; justify-content: center; gap: 12px;
    background: rgba(6,8,12,0.96); backdrop-filter: blur(16px);
    border-radius: 0; border: none; padding: 24px;
  }
  .topnav.open .topnav-link { font-size: 20px; padding: 14px 32px; }
  .hamburger { display: flex; }
  .hero-layout { padding: 24px; }
  .epoch-panel { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .economy-grid { grid-template-columns: 1fr; }
  .section-head { flex-direction: column; align-items: flex-start; }
  .table-tools { flex-direction: column; width: 100%; }
  .input.search { width: 100%; }
  .input.select { width: 100%; }
  .hero-status-card { width: 100%; }
  .hero-layout { padding: 20px; }
  .big-number { font-size: 34px; }
  .kpi-value { font-size: 28px; }
  .section { margin-bottom: 40px; }
}

/* ============ Reduced Motion ============ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .kpi-card:hover, .roadmap-card:hover { transform: none; }
  .progress-fill::after { animation: none; }
}

/* ============ Hamburger (hidden on desktop) ============ */
.hamburger {
  display: none; align-items: center; justify-content: center;
  width: 40px; height: 40px; border-radius: var(--radius-sm);
  background: var(--surface-2); border: 1px solid var(--border); cursor: pointer;
  color: var(--text-2); transition: color .18s ease;
}
.hamburger:hover { color: var(--text); }
.hamburger svg { width: 20px; height: 20px; }
```

- [ ] **Step 3: Verify in browser**

Loading overlay with gradient bar animation. Toast notifications. Responsive: resize browser to check 1200/900/640 breakpoints. Enable `prefers-reduced-motion` in DevTools to verify animations disabled.

- [ ] **Step 4: Commit**

```bash
git add dashboard/styles.css
git commit -m "feat(css): loading, toast, responsive, and reduced motion"
```

---

## Task 8: HTML Rewrite — Semantic Landmarks & A11y

**Files:**
- Modify: `dashboard/index.html` (rewrite)

**Interfaces:**
- Consumes: CSS classes from Tasks 1-7
- Produces: Semantic HTML with a11y attributes, mobile nav markup

- [ ] **Step 1: Rewrite index.html**

Replace the entire `index.html` with the new semantic structure. Key changes:
- Add `role="banner"` to header, `role="main"` to main
- Add `<nav aria-label="Primary">` for section nav
- Add skip link: `<a href="#main-content" class="skip-link">Skip to main content</a>`
- Add hamburger button for mobile nav
- Add `aria-label` on icon-only buttons
- Add `aria-live="polite"` on toast container and health pill
- Add `aria-sort` on sortable table headers
- Add `role="img" aria-label` on chart canvases
- Add `aria-hidden="true"` on decorative footer logo

The full HTML should match the existing structure but with these a11y additions. Copy from the current `index.html` and add the accessibility attributes.

- [ ] **Step 2: Verify in browser**

Page loads correctly. Tab through page — skip link appears on first Tab. Focus rings visible on all interactive elements. Screen reader announces landmarks.

- [ ] **Step 3: Commit**

```bash
git add dashboard/index.html
git commit -m "feat(html): semantic landmarks and accessibility attributes"
```

---

## Task 9: JS Enhancements — Stagger Animations, Mobile Nav, Scroll

**Files:**
- Modify: `dashboard/app.js` (modify existing)

**Interfaces:**
- Consumes: HTML structure from Task 8, CSS classes from Tasks 1-7
- Produces: Enhanced JS with stagger animations, mobile nav, scroll detection

- [ ] **Step 1: Add stagger animation observer**

At the end of the `init()` function in `app.js`, add:

```javascript
// Stagger section animations
if (window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(function (sec, i) {
    sec.style.opacity = '0';
    sec.style.transform = 'translateY(20px)';
    sec.style.transition = 'opacity 0.5s ease ' + (i * 80) + 'ms, transform 0.5s ease ' + (i * 80) + 'ms';
  });
  // Trigger after a short delay to allow initial render
  setTimeout(function () {
    sections.forEach(function (sec) {
      sec.style.opacity = '1';
      sec.style.transform = 'translateY(0)';
    });
  }, 100);
}
```

- [ ] **Step 2: Add mobile nav toggle**

Add to the `setupEvents()` function:

```javascript
// Mobile hamburger
var hamburger = document.querySelector('.hamburger');
var topnav = document.querySelector('.topnav');
if (hamburger && topnav) {
  hamburger.addEventListener('click', function () {
    var isOpen = topnav.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', isOpen);
    if (isOpen) {
      topnav.querySelector('.topnav-link').focus();
    }
  });
  // Close on Escape
  topnav.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && topnav.classList.contains('open')) {
      topnav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      hamburger.focus();
    }
  });
  // Close on link click
  topnav.querySelectorAll('.topnav-link').forEach(function (link) {
    link.addEventListener('click', function () {
      topnav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
    });
  });
}
```

- [ ] **Step 3: Add scroll-based topbar blur**

Add to the `setupEvents()` function:

```javascript
// Scroll-based topbar enhancement
var topbar = document.querySelector('.topbar');
if (topbar) {
  var scrollThreshold = 80;
  window.addEventListener('scroll', function () {
    if (window.scrollY > scrollThreshold) {
      topbar.classList.add('scrolled');
    } else {
      topbar.classList.remove('scrolled');
    }
  }, { passive: true });
}
```

- [ ] **Step 4: Verify in browser**

Page loads with staggered section fade-in. Hamburger appears at ≤900px, opens full-screen nav overlay. Topbar blur intensifies on scroll. All existing functionality (charts, table, exports) still works.

- [ ] **Step 5: Commit**

```bash
git add dashboard/app.js
git commit -m "feat(js): stagger animations, mobile nav, scroll blur"
```

---

## Task 10: Final Polish & Integration Test

**Files:**
- Modify: `dashboard/styles.css` (any remaining tweaks)
- Modify: `dashboard/index.html` (any remaining tweaks)
- Modify: `dashboard/app.js` (any remaining tweaks)

**Interfaces:**
- Consumes: All tasks 1-9
- Produces: Final polished dashboard

- [ ] **Step 1: Visual regression check**

Open the dashboard in browser at full width. Verify:
- Hero headline is large and commanding
- KPI grid is 4-column, cards hover with lift + gradient top-line
- Epoch progress bar has shimmer animation
- Charts render correctly in 2-column grid
- Economy cards in 4-column grid
- Validator table has zebra striping and sticky header
- Roadmap cards have colored left borders
- Footer renders with source chips

- [ ] **Step 2: Responsive check**

Resize browser through breakpoints:
- 1200px: KPI 2-col, economy 2-col, charts 1-col
- 900px: Nav collapses to hamburger, epoch stacks
- 640px: Everything 1-col, KPI values shrink

- [ ] **Step 3: Accessibility check**

- Tab through entire page — focus rings visible on all interactive elements
- Screen reader: landmarks announced correctly
- Skip link works
- Keyboard: can sort table headers, navigate pagination

- [ ] **Step 4: Reduced motion check**

Enable `prefers-reduced-motion: reduce` in DevTools. Verify all animations disabled, no transforms on hover.

- [ ] **Step 5: Final commit**

```bash
git add dashboard/
git commit -m "feat(dashboard): complete UI/UX redesign with a11y, motion, and responsive"
```
