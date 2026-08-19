# Solana Ecosystem Dashboard — Design Specification

**Document Version:** 2.0.0
**Target:** Superteam Canada Bounty Submission
**Theme:** Clean Institutional Dark Dashboard · Original Design

> This specification replaces v1.0.0, which was a 1:1 clone of a third-party
> template ("Coinstax"). That approach was removed because the bounty judges on
> **No Plagiarism** and **single-authentic visual identity**. v2.0.0 is an
> original design built from scratch: professional, airy, and readable with a
> strong emphasis on whitespace and clear visual hierarchy.

---

## 1. Design Philosophy

The dashboard is designed to feel like a **clinical institutional reporting
tool**, not a crypto "terminal skin". Every decision supports legibility and
trust:

- **Whitespace is a feature.** Cards breathe with generous internal padding
  (22–28px), sections are separated by 54px, and grid gutters are 18–20px.
- **Restraint over decoration.** One accent gradient (Solana purple → green),
  subtle surface elevation, and hairline borders — no fluorescent neon fills,
  no dense "trading terminal" wallpaper.
- **Data first.** Large tabular numerals, monospace for on-chain values, and
  sticky context labels. Everything a reviewer needs is one glance away.
- **Original.** No copied layout, tokens, or component inventory from a third
  party.

---

## 2. Color System

A deep, near-black navy base provides a quiet canvas; the signature Solana
`#9945FF → #14F195` gradient is used sparingly (progress, primary button, brand
ring) so accent reads as meaningful, not noise.

| Token | Hex | Purpose |
|---|---|---|
| `--bg` | `#07090D` | Page background |
| `--surface` | `#0E121A` | Cards, panels |
| `--surface-2` | `#141925` | Hover rows, inputs, subtler elevation |
| `--surface-3` | `#1B2230` | Tracks, chips, active nav |
| `--border` | `rgba(255,255,255,0.07)` | Hairline dividers |
| `--border-strong` | `rgba(255,255,255,0.15)` | Interactive borders |
| `--accent` | `#9945FF` | Eyebrows, focus, links, one ring |
| `--teal` | `#14F195` | Healthy status, active dots |
| `--accent-grad` | `linear-gradient(135deg,#9945FF,#14F195)` | Progress, primary CTA |
| `--up` | `#2FE6A2` | Positive deltas |
| `--down` | `#FF5C7A` | Negative deltas |
| `--warn` | `#FFB224` | Warnings |
| `--danger` | `#FF4D5C` | Critical |
| `--text` | `#ECEEF4` | Primary text |
| `--text-2` | `#9AA4B6` | Secondary labels |
| `--text-3` | `#67728A` | Muted, captions |
| `--text-dim` | `#49546A` | Disabled, meta |

Semantic status uses soft tinted pills (`--*-soft` backgrounds) for cluster
health, anomaly counts, delta chips, and validator states.

---

## 3. Typography

- **UI / Display:** `Inter` (400–800). `h1` at clamp(28px→40px)/800 tracks
  `-0.03em`; section `h2` at 24px/700.
- **Numerics:** `JetBrains Mono` + `font-variant-numeric: tabular-nums` for all
  on-chain values (TPS, slots, pubkeys, SOL amounts, fees) — zero layout shift.
- **Scale discipline** keeps density human: body 13px–16px, labels 11–12px,
  eyebrows 11px uppercase with `0.14em` tracking.

---

## 4. Information Architecture

A **five-tab, top-bar-driven layout** (Overview / Network / Validators / DeFi /
Economy) with a **sticky top bar** for persistent context:

1. **Top bar** — brand, section tabs, live cluster health pill, "updated x ago",
   and CSV / JSON / Refresh actions. Two hamburger reveals the actions on mobile.
2. **KPI grid** — stat cards (SOL price, TPS, slot time, validators, TVL) with
   inline SVG sparklines where data exists. The "at a glance" block.
3. **Network Performance panel** — epoch, block height, TPS, slot time, plus a
   live animated gradient **epoch progress bar**.
4. **Trends** — Chart.js charts (network throughput, SOL price, 30d TVL, active
   validators) from historical snapshots.
5. **Economic Indicators** — market cap, 24h volume, supply, median fee & REV.
6. **Top Validator table** — searchable and filterable (top-10 / Nakamoto set /
   0% commission / high commission), **paginated**, with CSV export.
7. **Roadmap** — upgrade cards with impact badges.
8. **Anomaly panel** — rule-driven alert feed with severity.
9. **Footer** — data sources, provenance, license.

---

## 5. Signature Elements

- **Live Pulse Orb** in the hero status card and the top-bar pill: animates at
  cluster health cadence, tinted by `--teal`/`--warn`/`--danger`.
- **Epoch progress bar** with an animated gradient fill driven by
  `epoch_progress_pct`.
- **Sparklines** rendered as zero-dependency inline SVG polylines in the KPI
  cards (no third-party canvas needed for at-a-glance trends).
- **Tabular mono numerics** throughout for professionals scanning fast.

---

## 6. Responsiveness

- ≤1200px: KPI grid 2-col, economy 2-col, charts single-col.
- ≤900px: top nav collapses, epoch panel stacks, tighter gutters.
- ≤640px: all content grids collapse to 1-col; table tools stack; font sizes
  step down (KPI value 24px).

---

## 7. Zero-Dependency Guarantee

No bundler, no framework, no `npm install`. The frontend is three static files —
`index.html`, `styles.css`, `app.js` — plus Chart.js loaded from CDN and Google
Fonts. It renders fully from the committed `report.json` regardless of network.
Background gradients and SVG assets are local; no API keys are ever required.
