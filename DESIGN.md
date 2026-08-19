# Solana Ecosystem Dashboard — Design Specification (Phase 0)

**Document Version:** 1.0.0  
**Target:** Superteam Canada Bounty Submission  
**Theme:** Solana High-Density Institutional Analytics & Trading-Terminal Hybrid

---

## 1. Color System (Dark Terminal Elevation)

Rather than pure `#000000` (which creates harsh contrast and flattens hierarchy) or generic `#1e1e2e`, we use a deep cosmic navy base (`#0B0E14`) with subtle surface tiering and authentic Solana brand accents:

| Token Name | Hex Code | Purpose & Application |
|---|---|---|
| `--bg-base` | `#080A0F` | Page background / deepest viewport layer |
| `--bg-surface` | `#0E121B` | Card surfaces & sidebar panel (subtle elevation, zero heavy borders) |
| `--bg-surface-elevated` | `#151B27` | Hover states, active table rows, modal / tooltip backings |
| `--border-subtle` | `rgba(255, 255, 255, 0.07)` | Hairline dividers and structural boundaries |
| `--border-focus` | `rgba(153, 69, 255, 0.4)` | Keyboard focus rings and active card boundaries |
| `--solana-purple` | `#9945FF` | Primary brand accent (gradients, hero badges, sparkline peaks) |
| `--solana-teal` | `#14F195` | Secondary brand accent, positive delta (+), active health pulse |
| `--solana-gradient` | `linear-gradient(135deg, #9945FF 0%, #14F195 100%)` | Logomark, hero accents, highlight bars |
| `--text-primary` | `#F3F4F6` | Display numbers, critical metrics, primary headings (95% white) |
| `--text-secondary` | `#9CA3AF` | Labels, table headers, subtitles, secondary metadata (60% gray) |
| `--text-muted` | `#6B7280` | Monospace pubkeys, slot heights, timestamp captions |
| `--delta-up` | `#14F195` | Positive price / TPS / stake growth pill badge (`rgba(20, 241, 149, 0.12)` bg) |
| `--delta-down` | `#FF4D6A` | Negative delta / drawdown pill badge (`rgba(255, 77, 106, 0.12)` bg) |
| `--status-healthy` | `#14F195` | RPC Healthy / Zero active critical anomalies |
| `--status-warning` | `#FFB020` | Moderate TPS drop, slot delay, or validator latency |
| `--status-critical` | `#FF3B30` | RPC outage, major delinquency spike (>5%), severe TVL shock |

---

## 2. Typography & Scale Hierarchy

To avoid the ubiquitous "generic Inter template" look, we combine a geometric characterful display typeface for hero numbers with high-legibility body type and a specialized tabular monospace:

- **Display Numbers / Hero Metrics:** `Syne` / `Space Grotesk`, sans-serif (wght 700/800) — distinctive wide geometric curves that evoke institutional fintech terminals.
- **UI & Table Body:** `Plus Jakarta Sans` / `Inter`, system fallback sans-serif (wght 400, 500, 600) — crystal-clear readability at 12px–13px data-table scale.
- **Tabular & On-Chain Data:** `JetBrains Mono` / `SF Mono`, monospace (wght 400, 500) with `font-variant-numeric: tabular-nums` — zero layout shift on live value changes, slot numbers, addresses, and vote pubkeys.

### Scale Discipline
- **Display 1 (Hero Metric Value):** 28px–32px, 700 wt, tracking -0.02em
- **Section Heading:** 16px, 600 wt, tracking -0.01em
- **Section Eyebrow / Small Caps Label:** 11px, 700 wt, `text-transform: uppercase`, tracking 0.08em
- **Table / Metric Body:** 13px, 400/500 wt, line-height 1.4
- **Table Monospace Data:** 12px, 500 wt, tabular figures
- **Micro Metadata / Footnotes:** 11px, 400 wt

---

## 3. Information Architecture & Layout Wireframe

### Desktop Viewport (1440px+)
```
+-------------------------------------------------------------------------------------------------------------------------+
| [LOGO] SOLANA ECOSYSTEM REPORT & DASHBOARD    [Live Pulse: Mainnet-Beta | 2400 TPS | SOL $184.20 (+4.2%) | Epoch 682 74%]   |  <- Ticker Strip
+------------------------------------+---------------------------------------------------------------+--------------------+
| SIDEBAR (240px fixed)              | MAIN CONTENT AREA (Flex-grow)                                 | RIGHT PANEL (320px)|
|                                    |                                                               |                    |
| > OVERVIEW                         | [Network Overview]  Last updated: 3 mins ago [Refresh Button] | [ANOMALY & ALERTS] |
|   - Hero Metrics                   |                                                               | [*] All Systems    |
|   - Real-time Health               | +-------------------+ +-------------------+ +---------------+ |     Normal         |
|                                    | | SOL PRICE         | | NETWORK TPS       | | ACTIVE NODES  | | - TPS: Healthy   |
| > NETWORK DYNAMICS                 | | $184.25  [+3.8%]  | | 2,482     [+1.2%] | | 1,428 [0.0%]  | | - Slot: 412ms    |
|   - Epoch Tracker                  | | [~~~~~ Sparkline] | | [~~~~~ Sparkline] | | [~~~ Sparkline| | - Delinq: 0.8%     |
|   - Slot / Block Time              | +-------------------+ +-------------------+ +---------------+ |                    |
|   - Vote Accounts & Stakes         |                                                               | [FEE & GAS METRIC] |
|                                    | [TOP VALIDATORS BY STAKE]                       [Search/Sort] | Median Tx Fee:     |
| > ECONOMIC & DEFI                  | +---+--------------------+-----------+--------+-------------+ | 0.000005 SOL       |
|   - Solana TVL ($6.4B)             | |#  | Validator Node     | Total SOL | Comm.  | Delta (7d)  | | [Bar Chart Trend]  |
|   - Stablecoins ($4.1B)            | | 1 | Jito Foundation 1  | 14.2M SOL | 5.0%   | +120k [~~~] | |                    |
|   - 24h DEX Volume                 | | 2 | Coinbase Cloud     | 11.8M SOL | 8.0%   |  -14k [~~~] | [NETWORK HEALTH]   |
|   - Real Economic Value (REV)      | | 3 | Figment Staking    |  9.4M SOL | 0.0%   |  +45k [~~~] | Slot: 284,912,410  |
|                                    | +---+--------------------+-----------+--------+-------------+ | Cluster: 100% ok   |
| > UPCOMING MILESTONES              |                                                               +--------------------+
|   - Alpenglow / SIMD-525           | [ECONOMIC INDICATORS & ECOSYSTEM FLOWS]                                            |
|                                    | +-------------------+ +-------------------+ +-------------------+ +--------------+ |
| [v1.0.0] [GitHub] [Raw JSON]       | | DeFi TVL: $6.42B  | | Stables: $4.18B   | | 24h DEX: $2.14B   | | REV: $1.82M/day| |
+------------------------------------+------------------------------------------------------------------------------------+
```

### Mobile Viewport (375px–640px)
```
+---------------------------------------+
| [=] [SOL LOGO] Solana Radar   [● LIVE]|  <- Compact Header + Drawer Trigger
+---------------------------------------+
| >>> Auto-scrolling Ticker Strip >>>   |  <- Horizontally scrollable
+---------------------------------------+
| Network Overview (Updated 3m ago)     |
|                                       |
| [ SOL Price: $184.25  (+3.8%)  [~~~] ]|
| [ Network TPS: 2,482   (+1.2%) [~~~] ]|
| [ Active Validators: 1,428     [~~~] ]|
+---------------------------------------+
| [!] ANOMALIES & HEALTH (Prioritized)  |
| Status: All Systems Operational (0)   |
+---------------------------------------+
| [ECONOMIC OVERVIEW CARDS (2x2 Grid)]  |
| - TVL: $6.42B      - Stables: $4.18B  |
| - DEX: $2.14B      - Rev: $1.82M/day  |
+---------------------------------------+
| [TOP VALIDATORS (Responsive Table)]   |
| # | Node               | Stake | 7d   |
| 1 | Jito Foundation 1  | 14.2M | +1.2%|
+---------------------------------------+
| [BOTTOM NAV BAR: Overview | Net | DeFi]
+---------------------------------------+
```

---

## 4. Signature Element: The "Ecosystem Velocity Orbital"

Rather than decorative clutter or generic crypto illustrations:
- **Visual Motif:** A high-precision CSS & Canvas micro-orbital halo around the Solana logomark in the header / ticker backdrop, with subtle particle nodes pulsing synchronously with the real Solana cluster TPS and slot duration.
- **Dynamic Live Pulse:** A dual-ring SVG pulse badge that pulses green (`#14F195`) at the exact cadence of the latest slot time (e.g. 400ms interval), turning amber or red if cluster latency exceeds 600ms.

---

## 5. Official Logo Asset Specification

The official Solana brand mark is rendered as a clean inline SVG with three rounded parallelograms and linear gradient (`#9945FF` -> `#14F195`). We place this SVG in `/dashboard/assets/solana-logo.svg` and embed it cleanly in `index.html`.

---

## 6. Self-Critique vs. Generic AI Dashboards & Reference Structure

1. **What we kept from the Reference:**
   - The high-density, multi-panel trading terminal structure: Left persistent sidebar, top continuous live ticker strip, 3-card live updates row with minimal embedded sparklines, sortable dense data table, and dedicated right-hand alerts & secondary indicator panel.
   - Strict typography discipline: 12px–13px data cells, tabular numbers, subtle pill badges for positive/negative deltas.

2. **What we adapted specifically for Solana's Brand & Ecosystem:**
   - Replaced generic crypto purple/blue with Solana's genuine dual-gradient (`#9945FF` to `#14F195`).
   - Adapted trading actions (Buy/Sell) into an actionable **Solana Anomaly & Alerts Engine** + **Network Velocity Monitor** (epoch progress, slot time, validator stake concentration, economic REV).
   - Ensured 100% zero-dependency execution: runs instantly without build steps or bundlers, while matching top-tier institutional fintech quality.
