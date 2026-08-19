# Solana Ecosystem Auto-Updating Report & Dashboard — Build Plan

**Bounty:** Superteam Canada — Develop Solana Ecosystem Auto-Updating Report & Interactive Dashboard
**Prize:** 500 / 300 / 200 USDG
**Deadline:** 3:59 AM, September 1, 2026 (UTC) — confirm this against the live listing before you lock your schedule
**Judging weights:** Comprehensiveness, Automation & Maintainability, Clarity & Presentation, Innovation, Technical Implementation

This doc is a set of copy-pasteable prompts for your coding agent, broken into phases. Run them **in order** — each phase assumes the previous one's files exist. Paste one phase at a time, let the agent finish and self-check, review the output, then move to the next. Don't paste all phases at once — that's how agents skip steps and you end up debugging a pile instead of a phase.

---

## Before you start: lock the architecture

Tell your agent this up front (or put it in a `CLAUDE.md` / `AGENTS.md` / project README) so it doesn't relitigate the stack every phase:

```
STACK DECISIONS — do not deviate without asking:
- Backend/data layer: Python 3.11+, stdlib only (urllib, json, sqlite3, datetime, dataclasses).
  No requests, no pandas, no external packages unless explicitly approved — the bounty
  rewards "no API keys/dependencies beyond stdlib and Solana RPC."
- Data sources: direct Solana JSON-RPC calls (public RPC endpoint, no key needed),
  DeFiLlama public API (no key), CoinGecko public API (no key). Dune Analytics is
  OPTIONAL/best-effort only since it requires an API key — do not block the pipeline on it.
- Output: the Python layer writes report.json, report.md, and a data/ directory of
  timestamped snapshots. It also renders a static dashboard: index.html + styles.css +
  app.js, reading from report.json. No frontend build step, no npm — vanilla JS,
  Chart.js loaded from CDN for charts.
- Storage: SQLite for historical snapshots (so we can show trend lines and detect anomalies
  over time, not just a single point-in-time read).
- Hosting target: GitHub Pages (static dashboard) + a GitHub Action that reruns the
  Python collector on a schedule and commits refreshed data. This IS the "automation"
  story for the judges — make it real, not aspirational.
- Repo will be public with a clear README — that's a hard submission requirement.
```

---

## Phase 0 — Design Direction (do this before any code)

Have the agent produce a design plan as a *document*, not code yet. This forces intentional choices instead of a generic dark dashboard.

**Reference layout to anchor on** (fintech/trading dashboard pattern — sidebar + ticker + live cards + data table + side action panel):

```
STRUCTURAL REFERENCE — build toward this exact information architecture, restyled for
Solana ecosystem data instead of trading:

- Persistent left sidebar: logomark + product name at top, grouped nav sections with
  small-caps section labels (e.g. "Overview" / "Network" / "Ecosystem" / "Other"), each
  item with an icon + label, active item highlighted with a filled pill background.
  A "Log out"-equivalent or settings item pinned at the bottom.
- Top ticker strip above the main content: a horizontal auto-scrolling or static row of
  key live values (SOL/USDC, TPS, active validators, epoch %) — small, dense, secondary
  to the hero, like a stock ticker.
- Content header: a "Welcome" / greeting-style eyebrow is optional for us (no user login
  here) — replace with the report's live status: "Network Overview" + "Last updated Xm
  ago" + a live-pulse indicator dot.
- "Live Updates" row: 3 compact cards side by side, each with a small label, a big number,
  a delta pill (green up / red down), and a tiny embedded sparkline/area chart beneath —
  use this pattern for the 3 most-watched live metrics (e.g. SOL price, current TPS,
  active validator count), not for every metric.
- Main data table below: sortable columns, each row showing an icon + name, then numeric
  columns (24h/7d/30d-style change columns become epoch/validator/economic deltas), with
  a tiny sparkline chart as the last column per row — reuse this exact table pattern for
  the top-validators-by-stake table and/or a multi-metric trend table.
- Right-hand panel (desktop only, stacks below content on mobile): a self-contained
  "action-style" card — repurpose this as an "Anomaly & Alerts" panel (status pill,
  current alert list or "All systems normal" state) sitting where the Buy/Sell panel
  is in the reference, plus a secondary card below it for a headline stat with an
  embedded candlestick/bar chart (repurpose as network activity or fee chart).
- Dense, data-forward feel: tight vertical rhythm, small type sizes for table data
  (12-13px), larger type reserved for hero numbers only. This is a trading-terminal
  density, not a marketing-page density — whitespace is used for separation between
  regions, not for padding every element generously.

This structure is proven and premium-reading; your job in this phase is to reskin it
around Solana ecosystem data and the Solana brand, not to invent a new IA from scratch.
```

Then have the agent produce the actual token/design plan:

```
Act as a design lead. Before writing any code, produce a short design plan for a premium,
professional Solana ecosystem dashboard following the structural reference above. I want
it to feel like a real trading/analytics product (a Solana-branded Nansen/Dune/trading-
terminal hybrid), not a generic AI-generated crypto template.

Give me:
1. COLOR — 5-6 named hex values. Anchor the accent system on Solana's real brand gradient
   (purple #9945FF to teal-green #14F195), on a near-black/near-navy base (not pure #000 —
   look at how the reference uses a very dark blue-grey, not flat black, for depth).
   Include a secondary neutral for card surfaces (subtle elevation via slightly lighter
   panel color, not borders), and a status set for anomaly alerts (healthy / warning /
   critical) plus the standard green-up/red-down delta convention from the reference.
2. TYPE — a display face for headline numbers (something with real character, not the
   default Inter-everywhere look) and a body face for labels/table data, plus a monospace
   for on-chain data (slot numbers, addresses, hashes, validator pubkeys) — the reference's
   table density means type scale discipline matters more than usual here.
3. LAYOUT — confirm the sidebar + ticker + live-cards + table + right-panel structure
   above, ASCII wireframe it at desktop AND mobile widths (sidebar collapses to a bottom
   nav or off-canvas drawer on mobile; ticker strip becomes horizontally scrollable;
   right panel stacks below the table).
4. SIGNATURE ELEMENT — the one memorable visual thing this dashboard will be remembered
   by. Consider: an orbital/globe motif representing "ecosystem" (validators/nodes as
   points orbiting a central Solana mark), used sparingly in the sidebar header or as a
   subtle background treatment behind the hero ticker — not a mascot, not decoration on
   every panel.
5. LOGO USAGE — use the real Solana logomark (fetch official SVG/brand assets from
   solana.com/branding, do not redraw or approximate it), placed in the sidebar header
   at the same weight/position the reference gives its own wordmark.

Critique your own plan against generic AI-dashboard defaults and against the reference
image — tell me specifically what you kept from the reference structure, what you changed
for Solana's brand, and why. Show me the plan before writing code.
```

Review this output yourself before moving on — this is the phase most worth your personal judgment, since it sets the ceiling for "Clarity & Presentation."

---

## Phase 1 — Project Scaffold

```
Set up the repo structure for the Solana Ecosystem Dashboard project:

/solana-ecosystem-dashboard
  /collector          <- Python stdlib data collection scripts
    rpc.py            <- Solana RPC calls
    onchain_metrics.py
    market_data.py    <- DeFiLlama, CoinGecko
    news.py           <- ecosystem news/announcements (best-effort, static-source list is fine)
    anomaly.py
    report_builder.py <- assembles report.json + report.md
    db.py             <- sqlite snapshot storage
    run.py            <- entrypoint, orchestrates the above
  /data
    snapshots.db       <- sqlite (gitignored if it gets large; keep a small sample committed)
    report.json         <- latest generated report
    report.md
  /dashboard
    index.html
    styles.css
    app.js
    /assets
      solana-logo.svg
  /.github/workflows
    refresh.yml         <- scheduled Action to rerun collector + commit + redeploy
  README.md
  LICENSE

Initialize git, write a .gitignore appropriate for Python (venv, __pycache__, .env), and
create a skeleton README with sections: Overview, Live Demo link (placeholder for now),
Architecture, Data Sources, How to Run, Automation Strategy, Anomaly Detection — I'll fill
content in as we build. Confirm the structure back to me before moving on.
```

---

## Phase 2 — On-chain Data Layer (Solana RPC)

```
Build collector/rpc.py using only Python stdlib (urllib.request, json). Implement a thin
JSON-RPC client against a public Solana mainnet-beta RPC endpoint (make the endpoint
configurable via an env var with a sane public default, and mention in comments that
production use should use a dedicated RPC provider to avoid rate limits).

Implement wrapper functions for:
- getSlot
- getBlockTime(slot)
- getEpochInfo
- getRecentPerformanceSamples (use this to compute current TPS and slot time)
- getVoteAccounts (active vs delinquent validator counts, stake distribution, top
  validators by stake, commission)
- getHealth
- getSupply

Then build collector/onchain_metrics.py which calls these and returns a single
structured dict/dataclass: network performance (TPS, avg slot time, block height, epoch
progress %), validator status (active/delinquent counts, top 10 by stake with commission,
stake distribution summary), and network health.

Handle RPC errors and timeouts gracefully — a single failed call should not crash the
whole collector; log it and return partial data with a clear "unavailable" marker so the
report/dashboard can show that instead of silently omitting it.

Add a __main__ block so I can run `python -m collector.onchain_metrics` and see the
output as pretty JSON to sanity check before wiring it into the full pipeline.
```

---

## Phase 3 — Off-chain Data Layer

```
Build collector/market_data.py (stdlib only) pulling from:
- DeFiLlama public API: Solana TVL (current + historical trend), stablecoin supply on
  Solana, DEX volume
- CoinGecko public API: SOL price, 24h change, market cap

Build collector/news.py: since Twitter/X requires paid API access now, don't try to
scrape it. Instead implement a lightweight, honest "ecosystem highlights" source: a
curated static list of key upcoming upgrades (Alpenglow, SIMD-525, etc. — pull current
facts via what you know plus any docs I paste in) with a clear "last updated" timestamp,
structured so it's easy for me to hand-edit weekly. Document in the code comments that
this is intentionally static/best-effort given API constraints, not silently pretending
to be live — that honesty matters more to judges than fake automation.

Compute derived economic indicators where possible from the above: median transaction
fee estimate (from recent performance samples + known fee model), Real Economic Value
proxy if you can derive one from available data (state your methodology in a comment if
you have to approximate — don't invent a number silently).

Same pattern as Phase 2: graceful per-source error handling, a __main__ block for
standalone testing, structured dataclass/dict output.
```

---

## Phase 4 — Storage + Report Compiler

```
Build collector/db.py: SQLite schema for storing timestamped snapshots of every metric
collected in Phases 2-3 (one row per collection run, JSON-serialized metrics blob plus a
few indexed columns for fast trend queries: timestamp, sol_price, tvl, tps, active_validators).
Include a function to fetch the last N snapshots for trend/sparkline data.

Build collector/report_builder.py which:
1. Runs the Phase 2 + Phase 3 collectors
2. Stores the snapshot via db.py
3. Pulls the last 30 days of snapshots for trend context
4. Assembles report.json — a single well-structured JSON document covering every metric
   category from the bounty scope, with a top-level "generated_at" timestamp and a
   "sources" list documenting exactly where each field came from
5. Renders report.md — a clean, human-readable Markdown report from the same data
   (use headers, tables for validator/economic data, a short prose summary at the top)

Build collector/run.py as the single entrypoint: `python run.py` should do a full
collection + storage + report generation cycle end to end, print a summary to stdout,
and exit with a nonzero code if any critical data source failed. Show me a sample
report.json and report.md after running it.
```

---

## Phase 5 — Anomaly Detection

```
Build collector/anomaly.py. Using the historical snapshots in SQLite, implement simple,
explainable anomaly detection (judges are grading "innovation" here, but explainable
beats black-box for a data-integrity dashboard):

- TPS drop/spike: flag if current TPS deviates more than N% from the trailing 7-day
  average (make N configurable, default something reasonable like 30%)
- Slot time: flag if avg slot time exceeds a sane threshold (~400-600ms baseline)
- Validator delinquency: flag if delinquent validator count or % jumps meaningfully
  vs the last snapshot
- TVL / SOL price: flag moves beyond N% in 24h

Each detected anomaly should produce a structured alert object: {metric, severity
(warning/critical), current_value, baseline_value, description in plain English}.
Wire this into report_builder.py so anomalies appear in both report.json (as an
"alerts" array) and report.md (as a highlighted section at the top if any are active).
Write a quick unit test with synthetic data that forces each anomaly type to trigger,
so I can verify the logic actually fires correctly, not just that it runs without error.
```

---

## Phase 6 — Dashboard Frontend (premium UI)

This is the highest-leverage phase for "Clarity & Presentation." Reference the Phase 0 design plan explicitly.

```
Build the static dashboard in /dashboard using the design plan from Phase 0, following
the structural reference (sidebar + ticker + live-cards + table + right panel) exactly.
Read report.json at load time (fetch it as a static file — no backend server needed) and
render:

LAYOUT
- Left sidebar: Solana logomark (real SVG) + product name, nav sections "Overview",
  "Network", "Ecosystem", "Alerts" with icons, active-item pill highlight, settings/repo
  link pinned at bottom. This is mostly a single-page dashboard, so nav items can scroll
  to page sections (anchor links) rather than routing — keep it functional, not decorative.
- Top ticker strip: horizontal row of compact live values — SOL price, current TPS,
  active validators, epoch progress % — small text, delta arrows, subtle divider dots
  between items. Marquee/auto-scroll on mobile if it overflows, static row on desktop.
- Content header: "Network Overview" + live-pulse dot + "Last updated Xm ago" (compute
  from report.json's generated_at against current time client-side).
- "Live Updates" row: exactly 3 cards — SOL price, current TPS, active validator count.
  Each: label, big number, green/red delta pill vs previous snapshot, small embedded
  sparkline (Chart.js, no axes/gridlines, just the line — matches the reference's minimal
  embedded chart style).
- Main table: top validators by stake. Columns: rank, validator (name/pubkey truncated +
  small identicon or generic node icon), stake amount, commission %, delta vs last
  snapshot, and a sparkline column showing recent stake trend if you have the history for
  it (fall back to a static trend icon if not). Sortable column headers.
- Second table or card cluster below: economic indicators (TVL, stablecoin supply, DEX
  volume, median fee) and ecosystem growth (tokenized asset volume, daily active
  addresses) — reuse the same dense row style as the validator table where it fits,
  cards where a single number tells the story better.
- Right panel (desktop; stacks below main content on mobile, above the footer):
  - Top card: "Alerts" — status pill (All systems normal / N active alerts), list of
    active anomalies from report.json's alerts array with severity color coding, or the
    all-clear state
  - Second card: a headline chart (network activity or fee trend) using a bar/candlestick-
    style Chart.js chart styled with the brand gradient, echoing the reference's chart
    panel weight and position
- Footer: data source attribution (RPC endpoint, DeFiLlama, CoinGecko), link to GitHub
  repo, links to raw report.json/report.md, upcoming-upgrades list (Alpenglow, SIMD-525
  etc.) as a simple text list since it doesn't need its own major panel

RESPONSIVENESS
- Design mobile-first, then scale up: single column on mobile (<640px) with sidebar
  collapsed to a bottom nav or off-canvas drawer, ticker strip horizontally scrollable;
  2-column on tablet (640-1024px); full sidebar + multi-column layout on desktop
  (>1024px). Test the layout logic explicitly at 375px, 768px, and 1440px widths.
- On mobile, the right panel (alerts + chart) stacks directly below the live-updates row,
  ahead of the full validator table, so the most important status info isn't buried below
  a long scroll.
- Charts must resize/reflow on mobile, not overflow or get clipped. Table columns should
  collapse gracefully (hide less-critical columns, e.g. commission %, below tablet width
  rather than horizontally scrolling the whole table).

QUALITY BAR
- Visible keyboard focus states on all interactive elements
- Respect prefers-reduced-motion for any transitions/animations
- No layout shift while report.json loads — use skeleton states, not a blank flash
- Take this seriously as a real product surface: consistent spacing scale, consistent
  corner radii, no orphaned/oversized whitespace, no default browser button styling
  left unstyled anywhere

Build it, then critique your own output against the Phase 0 plan — tell me anywhere you
had to deviate and why, and anywhere it still reads generic so we can fix it before I
review.
```

If you have a `visualize`/design tool available to your agent, this is also a good phase to ask it to render a static preview screenshot before you commit to full implementation — catch layout problems before they're wired to real data.

---

## Phase 7 — Automation (the judging criterion most submissions half-ass)

```
Build .github/workflows/refresh.yml: a GitHub Action that
1. Runs on a schedule (cron — pick something reasonable like every 6 hours, configurable)
2. Checks out the repo, sets up Python (stdlib only, so no dependency install needed
   beyond the interpreter itself)
3. Runs `python run.py`
4. Commits the updated data/report.json, data/report.md, and data/snapshots.db back to
   the repo if they changed
5. If the repo is deployed via GitHub Pages from this branch, the commit alone triggers
   a redeploy — confirm the Pages config does this, or add an explicit deploy step

Also add a `workflow_dispatch` trigger so I can manually re-run it on demand for a live
demo during judging. Show me the final YAML and a plain-English explanation of exactly
what happens on each run, since I need to explain the "automation strategy" clearly in
the README and the judges will read this file too.
```

---

## Phase 8 — Docs, Deploy, and Submission Polish

```
Finalize the README.md with all required sections filled in for the bounty submission:
- Overview + screenshot of the dashboard (desktop and mobile)
- Live demo link (GitHub Pages URL once deployed)
- Architecture diagram (ASCII is fine) showing collector -> SQLite -> report.json/md ->
  static dashboard -> GitHub Action loop
- Data sources used and exactly how each is integrated (be specific: which RPC methods,
  which DeFiLlama/CoinGecko endpoints)
- Automation strategy (reference the Action from Phase 7 in plain English)
- Anomaly detection methodology (reference Phase 5, explain the thresholds honestly)
- Limitations section — be upfront about what's best-effort (Dune, X/Twitter sentiment)
  rather than overclaiming; judges checking "no plagiarism / originality" will trust a
  submission more if it's honest about scope
- "How to run locally" — exact commands, should work from a clean clone with zero setup
  beyond a Python interpreter

Then:
1. Enable GitHub Pages on the /dashboard directory (or a docs/ copy if Pages requires it)
2. Run the collector once manually to generate a real, non-empty report.json/report.md
   before I submit, so the live demo isn't showing empty state
3. Double check report.json and report.md are both present in the repo and linked from
   the README, since the bounty explicitly asks for samples of both
4. Give me a final checklist mapped against the bounty's exact submission requirements
   (repo link, README, live demo, sample reports, write-up) so I can verify nothing's
   missing before I submit.
```

---

## Submission checklist (map back to the bounty text)

- [ ] Public GitHub repo, clean commit history, clear README
- [ ] Live/hosted dashboard link (GitHub Pages)
- [ ] Sample `report.json` and `report.md` committed and linked
- [ ] Write-up: data sources + integration method, automation strategy, anomaly detection, run instructions
- [ ] Dashboard is dark-theme, responsive, premium — not a generic template
- [ ] Real Solana logomark used correctly, no redrawn/approximated logo
- [ ] No API keys required to run it
- [ ] Everything actually runs from a clean clone — test this yourself, don't take the agent's word for it

Good luck — this is a strong scope for you given the Grim/BlackArch container work you've already been doing with Python + local tooling under constrained hardware. The main risk is time, not skill: keep each phase's review tight so you're not debugging three phases' worth of drift at once.
