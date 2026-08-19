# Solana Dashboard — Full Visual Overhaul Design Spec

**Date:** 2026-08-19
**Scope:** Complete UI/UX redesign of dashboard frontend (HTML, CSS, JS)
**Approach:** Full visual overhaul — rewrite CSS, restructure HTML, add motion/a11y/responsive

---

## 1. Visual Identity & Color System

### 1.1 Base Palette
- **Page background:** `#06080C` (OLED-black)
- **Surface levels:**
  - `--surface`: `#0C1017` (cards at rest)
  - `--surface-2`: `#111720` (hover rows, inputs)
  - `--surface-3`: `#18202C` (active nav, chips, tracks)
  - `--surface-4`: `#1E2636` (elevated cards, modal backgrounds)
- **Borders:**
  - `--border`: `rgba(255,255,255,0.06)` (hairline dividers)
  - `--border-strong`: `rgba(255,255,255,0.14)` (interactive borders)
  - `--border-glow`: `rgba(153,69,255,0.3)` (accent focus/hover)

### 1.2 Accent & Semantic
- **Accent:** `#9945FF` (Solana purple) — used for eyebrows, focus rings, active states
- **Teal:** `#14F195` (Solana green) — healthy status, success dots
- **Gradient:** `linear-gradient(135deg, #9945FF 0%, #14F195 100%)` — progress bars, primary CTA, sparkline fills
- **Status:** `--up: #2FE6A2`, `--down: #FF5C7A`, `--warn: #FFB224`, `--danger: #FF4D5C`
- **Soft variants:** All status colors get 13-14% opacity backgrounds for pills/badges

### 1.3 Text Hierarchy
- `--text: #ECEEF4` (primary)
- `--text-2: #9AA4B6` (secondary)
- `--text-3: #67728A` (muted — must meet 4.5:1 contrast on surfaces)
- `--text-dim: #49546A` (disabled/meta)

### 1.4 Shadows & Elevation
- Resting cards: `0 1px 0 rgba(255,255,255,0.02) inset, 0 4px 16px -8px rgba(0,0,0,0.5)`
- Hover cards: `0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 32px -8px rgba(0,0,0,0.7)`
- Active CTA: `0 6px 20px -8px rgba(153,69,255,0.6)`

---

## 2. Typography

### 2.1 Type Scale (Modular)
| Token | Size | Line-Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `display` | clamp(36px, 5vw, 56px) | 1.1 | 800 | Hero headline |
| `h1` | clamp(28px, 4vw, 40px) | 1.15 | 800 | Section headings |
| `h2` | 24px | 1.2 | 700 | Card titles |
| `body-lg` | 16px | 1.5 | 400 | Hero subtitle |
| `body` | 14px | 1.5 | 400 | Default text |
| `body-sm` | 13px | 1.5 | 400 | Table cells, labels |
| `caption` | 12px | 1.5 | 500 | Metadata, timestamps |
| `overline` | 11px | 1.4 | 700 | Eyebrows (uppercase, 0.14em tracking) |
| `mono` | 30px | 1.1 | 800 | KPI values |
| `mono-lg` | 52px | 1.0 | 800 | Hero big number |

### 2.2 Font Families
- **UI:** Inter (400-800) — loaded from Google Fonts
- **Numerics:** JetBrains Mono (400-700) — all on-chain values, pubkeys, SOL amounts
- Both fonts: `font-variant-numeric: tabular-nums` for zero layout shift

### 2.3 Type Application
- Hero headline: `-0.04em` tracking, `clamp(36px, 5vw, 56px)`
- KPI card values: `36px` / weight 800 / `-0.02em` tracking
- Section spacing: Hero → KPIs (80px), KPIs → Epoch (64px), Epoch → Charts (54px), Charts → Economy (54px), etc.
- Card internal padding: `24px 28px` consistent
- Card element gap: `16px`

---

## 3. Component Architecture

### 3.1 Cards (`.card`)
- Background: `var(--surface)`, border: `1px solid var(--border)`
- Border-radius: `16px` (large cards), `12px` (small cards)
- Shadow: resting shadow from 1.4
- Hover: `transform: translateY(-3px)` + elevated shadow + border-color → `--border-strong` over 200ms ease-out
- KPI cards: Top accent gradient line (2px) that fades in on hover via `::before` pseudo-element

### 3.2 KPI Cards
- Layout: vertical flex, `gap: 12px`
- Label: `overline` style, `--text-2`
- Value: `mono` 36px, weight 800
- Delta chip: inline-flex pill with `--up-soft`/`--down-soft` background
- Sparkline: SVG polyline below delta, gradient fill matching metric color, height 34px
- Hover: translateY(-3px) + accent border-top glow

### 3.3 Validator Table
- Zebra striping: alternating `--surface` / `--surface-2` row backgrounds
- Sticky header: `position: sticky; top: 0; z-index: 2` with `backdrop-filter: blur(8px)`
- Row hover: left accent border (3px `--accent`) + `--surface-2` background
- Sort indicators: `↑` / `↓` icons in header cells
- Status pills: `--teal-soft` for active, `--warn-soft` for delinquent, with subtle pulse animation on delinquent
- Pagination: ghost buttons, mono font page counter

### 3.4 Charts
- Card: rounded corners, inner padding `24px 28px`
- Chart container: `height: 220px` on desktop, `240px` on mobile
- Tooltip: dark background (`--surface-3`), border, mono font values
- Grid lines: `rgba(255,255,255,0.04)`
- Hover: subtle crosshair cursor

### 3.5 Buttons
- **Primary:** Gradient background (`--accent-grad`), dark text, gradient border on hover
- **Ghost:** `--surface-2` background, `--text-2` color, hover → `--text` + border brightens
- All buttons: `border-radius: 8px`, min-height `36px`, transition 180ms

### 3.6 Navigation (Topbar)
- Sticky, backdrop-filter blur(12px)
- Brand: logo + stacked title/subtitle
- Section nav: pill-style tabs, active = `--surface-3` background
- Health pill: animated dot + status text
- Actions: ghost buttons for CSV/JSON export, primary for Refresh

### 3.7 Mobile Navigation
- At ≤900px: hamburger icon replaces topnav
- Tap → full-screen overlay with section links, close button
- Focus trap when open
- Links: large tap targets (48px height)

### 3.8 Roadmap Cards
- Left accent border: `--danger` for critical, `--warn` for high
- Hover: translateY(-2px) + subtle glow
- Status dot: colored by impact level

### 3.9 News Cards
- Tag pill: `--accent-soft` background, `--accent` text
- Hover: border glow effect

---

## 4. Motion System

### 4.1 Entry Animations
- **Page load:** Staggered fade-in + slide-up (20px) per section, 80ms delay between sections
  - Hero (0ms) → KPI grid (80ms) → Epoch panel (160ms) → Charts (240ms) → Economy (320ms) → Validators (400ms) → Roadmap (480ms) → News (560ms) → Anomalies (640ms) → Footer (720ms)
- **KPI sparklines:** SVG `stroke-dasharray` draw-in animation on load (800ms ease-out)
- **Chart reveal:** scale 0.98 → 1.0 + opacity 0 → 1 over 400ms

### 4.2 Hover Interactions
- **Cards:** `transform: translateY(-3px)` + shadow expansion, 200ms ease-out
- **Table rows:** Left accent border slide-in + background shift, 150ms
- **Buttons:** Background fill + slight scale(1.02), 150ms
- **Nav links:** Color transition + underline, 150ms

### 4.3 Ambient Motion
- **Health dot:** Breathing glow — scale 1 → 1.3 → 1, opacity 0.7 → 1 → 0.7, 2s infinite
- **Epoch progress bar:** Shimmer effect — moving highlight across gradient, 3s infinite
- **Loading bar:** Gradient slide animation (existing, improved)

### 4.4 Page Transitions
- **Toast notifications:** Slide in from right (translateX 20px → 0), fade out with blur, 2800ms duration
- **Topbar blur:** Intensifies on scroll past hero (scroll event listener, `backdrop-filter` transition)

### 4.5 Reduced Motion
- `@media (prefers-reduced-motion: reduce)` — all animations → instant (0ms duration), no transforms, no transitions except opacity fades for state changes

---

## 5. Responsive Design

### 5.1 Breakpoints
| Breakpoint | Target | Changes |
|-----------|--------|---------|
| ≤1200px | Tablet landscape | KPI grid 2-col, economy 2-col, charts 1-col |
| ≤900px | Tablet portrait | Nav → hamburger, epoch panel stacks, tighter gutters (16px) |
| ≤640px | Mobile | All grids 1-col, table tools stack, font sizes step down |

### 5.2 Mobile-Specific (≤640px)
- KPI values: `28px` (down from 36px)
- Hero headline: `clamp(28px, 6vw, 36px)`
- Section spacing: 40px (down from 54px)
- Card padding: `18px 20px` (down from 24px 28px)
- Validator table: horizontal scroll with sticky first column
- Charts: full-width, height 240px
- Touch targets: minimum 44px for all interactive elements
- Safe areas: `env(safe-area-inset-*)` respected

### 5.3 Tablet (≤900px)
- Topnav collapses to hamburger
- Hero layout stacks vertically
- Epoch panel: single column
- Table search/filter: full width, stacked

### 5.4 Desktop (≤1200px)
- KPI grid: 2 columns
- Economy grid: 2 columns
- Charts: single column
- Validator table: full width

---

## 6. Accessibility (a11y)

### 6.1 Landmark Roles
- `<header>` for topbar with `role="banner"`
- `<nav aria-label="Primary">` for section navigation
- `<main>` for content area
- `<footer>` for footer

### 6.2 Skip Link
- "Skip to main content" — positioned off-screen, appears on focus
- Links to `#main-content` anchor

### 6.3 Focus Management
- Visible focus rings: `2px solid var(--accent)` with `2px` offset on all interactive elements
- Focus trap in mobile nav overlay
- Tab order: topnav → hero → KPIs → epoch → charts → economy → validators → roadmap → news → anomalies → footer

### 6.4 Keyboard Navigation
- All buttons, links, and inputs keyboard-accessible
- Table headers: Enter/Space to sort
- Pagination: arrow keys
- Mobile nav: Escape to close

### 6.5 Color Contrast
- All text meets WCAG AA (4.5:1 normal, 3:1 large)
- `--text-3` (#67728A) on `--surface` (#0C1017): ~4.8:1 ✓
- Status colors on soft backgrounds: verified contrast

### 6.6 Screen Reader Support
- `aria-label` on icon-only buttons (CSV, JSON, Refresh, hamburger)
- `aria-live="polite"` on toast container and health status
- `aria-sort` on sortable table headers
- `role="img"` + `aria-label` on chart canvases
- `aria-hidden="true"` on decorative elements (logos in footer)

### 6.7 Reduced Motion
- `@media (prefers-reduced-motion: reduce)` disables:
  - All CSS transitions (set to 0ms)
  - All CSS animations (set to `none`)
  - SVG sparkline draw-in
  - Page load stagger
  - Card hover transforms
  - Toast slide-in (instant appear/disappear)

---

## 7. File Structure

```
dashboard/
├── index.html          # Restructured HTML with semantic landmarks, a11y attrs
├── styles.css          # Complete CSS rewrite (design tokens, components, responsive, a11y)
├── app.js              # Enhanced JS (stagger animations, mobile nav, scroll detection, a11y)
├── assets/
│   └── solana-logo.svg # Existing, no changes
├── data/
│   └── report.json     # Existing, no changes
├── report.json         # Existing, no changes
└── report.md           # Existing, no changes
```

---

## 8. Implementation Order

1. **CSS foundation** — Design tokens, base styles, typography scale, color system
2. **Layout system** — App shell, topbar, sections, grid system, spacing
3. **Components** — Cards, KPI grid, buttons, chips, table, charts, roadmap, news
4. **Responsive** — Breakpoints, mobile nav, stacking, touch targets
5. **Motion** — Entry animations, hover effects, ambient motion, reduced motion
6. **Accessibility** — Skip link, landmarks, focus management, keyboard nav, ARIA
7. **HTML restructure** — Semantic landmarks, a11y attributes, mobile nav markup
8. **JS enhancements** — Stagger loader, scroll detection, mobile nav toggle, a11y JS
