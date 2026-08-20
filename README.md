# ⚡ Solana Ecosystem Intelligence — Auto-Updating Report & Dark Terminal

> **Superteam Canada · 1,000 USDG · Regional (Canada) · 11 submissions · Due Sep 1, 2026**
> **Bounty:** *Develop Solana Ecosystem Auto-Updating Report & Interactive Dashboard* — comprehensive, automated, original

[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](run.py)
[![Stdlib Only](https://img.shields.io/badge/stdlib-only-brightgreen)](collector/)
[![No API Keys](https://img.shields.io/badge/API_keys-none-success)](SECURITY.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Vercel](https://img.shields.io/badge/Vercel-live-black?logo=vercel)](https://dashboard-flame-gamma-14.vercel.app)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-181717?logo=github)](https://edgywol.github.io/Solana_Ecosystem/)

| | Link |
|---|---|
| **Repository** | [github.com/Edgywol/Solana_Ecosystem](https://github.com/Edgywol/Solana_Ecosystem) |
| **Live Demo — Vercel (primary, auto-deploy)** | **[dashboard-flame-gamma-14.vercel.app](https://dashboard-flame-gamma-14.vercel.app)** |
| **Live Demo — GitHub Pages** | [edgywol.github.io/Solana_Ecosystem](https://edgywol.github.io/Solana_Ecosystem/) |
| **Machine JSON** | [`data/report.json`](data/report.json) |
| **Human Markdown** | [`data/report.md`](data/report.md) |

![Dashboard Preview](docs/screenshot-desktop.png)

---

## 🌟 Submission Highlights & Key Differentiators

- **Zero External Dependencies:** Built with **Python 3.11+ Standard Library only** (`urllib`, `json`, `sqlite3`, `datetime`, `dataclasses`). **No `pip install`, no node_modules, no API keys needed.**
- **Direct On-Chain Telemetry:** JSON-RPC client directly against Solana mainnet-beta with automatic gzip decompression and multi-endpoint failover.
- **Explainable Anomaly & Risk Engine:** Predictive statistical engine that fits an exponential-smoothing trend baseline to trailing SQLite snapshots and flags deviations in σ from that trend (TPS shocks, slot latency, SOL price/volatility, TVL drawdowns), plus hardcoded safety checks for cluster health, validator delinquency, and a multi-metric "network stress" composite.
- **Professional, Original UI:** Clean institutional dark design built from scratch — generous whitespace, clear hierarchy, status pill, KPI cards with inline SVG sparklines, four Chart.js trend charts, a live epoch progress bar, and a searchable/filterable/paginated validator table with CSV export. No third-party template or skin is copied (see `DESIGN.md`).
- **Measured economics & real social signal, not assumed:** median transaction fees are derived live from `getRecentPrioritizationFees` RPC samples (with an explicit model fallback when sampling is unavailable). **Community sentiment** is pulled live from CoinGecko's crowd-sentiment vote + a keyless RSS cascade (Nitter → GitHub Atom), and **Daily Active Addresses** is estimated from a real RPC signature sample rather than invented. Only tokenized equities remain honestly declared in `coverage.not_collected`; Dune is now **cache-first** (`data/dune_cache.json` live-refreshes on `DUNE_API_KEY`).
- **Live Price While Provenance Stays Honest:** Dashboard polls CoinGecko `simple/price` every 60s in the browser — a drop at 14:05 shows at 14:06 with a `· LIVE ·` badge, while `Generated at` in `report.json` remains the auditable backend stamp.
- **Complete Automation Loop:** Scheduled GitHub Action (`refresh.yml`) running every 6 hours and on-demand via `workflow_dispatch`, committing refreshed snapshots and auto-deploying to **GitHub Pages + Vercel** (connected repo, `outputDirectory: dashboard`).

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------------------------------+
|                                      DATA INGESTION LAYER                                     |
|                                                                                               |
|   +-----------------------------+   +---------------------------+   +---------------------+   |
|   |      Solana JSON-RPC        |   |      DeFiLlama Public     |   |    CoinGecko Free   |   |
|   |  (TPS, Slots, Stakes, Node, |   |    (TVL, 30d Hist, DEX)   |   | (Spot Price, 24h,   |   |
|   |        Signatures/DAA)       |   |                           |   |  Crowd Sentiment)   |   |
|   +--------------+--------------+   +-------------+-------------+   +----------+----------+   |
+------------------|--------------------------------|----------------------------|--------------+
                   |                                |                            |
                   +------------------------> + <---+----------------------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------------+
|                                PYTHON STDLIB COLLECTOR PIPELINE                               |
|                                                                                               |
|   1. collector/rpc.py               -> Resilient JSON-RPC client with gzip/deflate decoding   |
|   2. collector/onchain_metrics.py   -> Throughput, epoch progress, validator stake & Nakamoto |
|   3. collector/market_data.py       -> Spot prices, DeFi capital turnover & Real Economic Val |
|   4. collector/news.py              -> Curated technical upgrade & SIMD roadmap tracker       |
|   5. collector/anomaly.py           -> Predictive exponential-smoothing anomaly engine        |
|   6. collector/db.py                -> SQLite persistent timeseries snapshot storage          |
|   7. collector/report_builder.py    -> Dual-format report compiler (JSON + Markdown)          |
|   8. collector/community_sentiment.py -> Real crowd sentiment (CoinGecko, no API key)         |
|   9. collector/daily_active_addresses.py -> Real RPC-sampled DAA estimate (no API key)         |
+---------------------------------------------+-------------------------------------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
+---------------------------------------------+   +---------------------------------------------+
|               STORAGE & FEEDS               |   |            INTERACTIVE DASHBOARD            |
|                                             |   |                                             |
|   - data/snapshots.db (SQLite Timeseries)   |   |   - dashboard/index.html (Vanilla UI)       |
|   - data/report.json  (Machine-Readable)    |-->|   - dashboard/styles.css (Clean Dark Theme) |
|   - data/report.md    (Human-Readable)      |   |   - dashboard/app.js     (Chart.js CDN)     |
+---------------------------------------------+   +---------------------------------------------+
                       ^
                       |
+-----------------------------------------------------------------------------------------------+
|                       AUTOMATION ENGINE (.github/workflows/refresh.yml)                       |
|                                                                                               |
|   - Scheduled Cron (Every 6 hours) + Manual on-demand dispatch (workflow_dispatch)            |
|   - Executes python run.py -> Commits updated snapshots -> Deploys GitHub Pages               |
+-----------------------------------------------------------------------------------------------+
```

---

## 🌐 Data Sources & Methodology

| Data Category | Provider / Endpoint | Methods / Fields | Integration Details |
|---|---|---|---|
| **Consensus & Performance** | `api.mainnet-beta.solana.com` | `getSlot`, `getBlockTime`, `getEpochInfo`, `getRecentPerformanceSamples` | Samples 30–60 performance windows to derive current TPS, true non-vote TPS, 15m average TPS, and average slot duration in ms. |
| **Validators & Decentralization** | `api.mainnet-beta.solana.com` | `getVoteAccounts` (with gzip) | Ingests active and delinquent vote accounts, calculates active stake in SOL, and computes the **Nakamoto Coefficient** (minimum validators required to control 33.3% of stake). |
| **Cluster Health & Supply** | `api.mainnet-beta.solana.com` | `getHealth`, `getSupply` | Checks node health and calculates circulating vs staked SOL supply ratio. |
| **DeFi & Liquidity** | `api.llama.fi`, `stablecoins.llama.fi` | `/v2/chains`, `/historicalChainTvl/Solana`, `/overview/dexs/solana`, `/stablecoinchains` | Ingests live Solana TVL, trailing 30-day historical TVL series, 24h DEX volume, and USD stablecoin market cap. |
| **Market Valuation** | `api.coingecko.com` (Binance fallback) | `/simple/price?ids=solana` | Ingests SOL/USD spot price, 24h price percentage change, market cap, and 24h volume. |
| **Real Economic Value (REV)** | Derived Economic Metric | Calculated in `collector/market_data.py` | Transparent proxy formula: `(Estimated Daily Non-Vote Tx * Median Fee USD) + Daily Jito MEV Tip Flow`. |
| **Community Sentiment** | `api.coingecko.com` | `/coins/solana?...&community_data=true` | Live crowd-sentiment vote (`sentiment_votes_up_percentage`), community-data counts (Telegram followers), and SOL 24h momentum. **No API key.** Correlated against on-chain momentum in `collector/community_sentiment.py`. |
| **Daily Active Addresses (DAA)** | `api.mainnet-beta.solana.com` | `getSignaturesForAddress` + `getTransaction` | RPC-sampled fee-payer uniqueness across high-coverage programs, extrapolated to a clearly-labeled **modeled lower bound** from daily non-vote transaction volume. **No API key.** Full methodology in `collector/daily_active_addresses.py`. |
| **Dune Analytics** | `dune.com` + `api.dune.com` | `v1/query/{id}/results` | Cache-first snapshot (`data/dune_cache.json`) with live refresh when `DUNE_API_KEY` set. No key required to run. See `collector/dune.py`. |
| **Social Ingest (Twitter/X proxy)** | `nitter.net` / `github.com` Atom | `RSS/Atom` | Keyless RSS cascade: tries Nitter RSS, falls back to Solana SIMD GitHub Atom with sentiment tags. Never fabricated; reports `unavailable` if all endpoints 403. See `collector/social_ingest.py`. |
| **Protocol Roadmap** | Hand-Curated Technical Ledger | `collector/news.py` | Curated technical upgrade ledger covering Alpenglow, Firedancer, SIMD-0096, and SIMD-0123. |

---

## 🚨 Anomaly Detection Engine

The anomaly detection engine (`collector/anomaly.py`) uses explainable, deterministic statistical checks against historical snapshots:

```python
# Core Anomaly Rules Evaluated on Every Run:
1. Predictive TPS trend: fits an exponential-smoothing trend to trailing snapshots;
   flags if current TPS deviates >2σ (Warning) or >3.5σ (Critical) from the trend line.
2. Slot Duration: flags if average slot time exceeds 550ms (Warning) or 750ms (Critical) vs 400ms target.
3. Delinquency Spike: flags if delinquent validator stake exceeds 2.0% of total active stake.
4. SOL Price / Volatility: flags >2σ deviation from the smoothed momentum baseline, plus
   hardcoded >10% (Warning) / >20% (Critical) absolute 24h moves.
5. TVL Drawdown: flags >10% 24h DeFi TVL drop.
6. Cluster Health: flags if RPC health status is degraded or connectivity fails.
7. Network Stress (composite): a WARN/CRITICAL risk index blending recent TPS drop,
   slot-time rise, and TVL drawdown into one headline stress score.
```

Active alerts appear in both `report.json` (as structured alert objects) and `report.md` (as highlighted callout blocks), and render with severity badges in the dashboard's Anomaly Panel.

---

## 🤖 Automation Strategy

The workflow in [`.github/workflows/refresh.yml`](.github/workflows/refresh.yml) guarantees consistent, scheduled intelligence delivery:
1. **Trigger:** Runs automatically on cron every 6 hours (`0 */6 * * *`) and on manual `workflow_dispatch` for live demos.
2. **Execution:** Standard Ubuntu runner spins up Python 3.11 and executes `python3 run.py`.
3. **Commit:** Changes to `data/report.json`, `data/report.md`, and `data/snapshots.db` are automatically committed to `main` with `[skip ci]`.
4. **Deploy:** Uses `actions/deploy-pages@v4` to immediately deploy the updated static dashboard to GitHub Pages.

---

## 💻 How to Run Locally (Zero Setup)

### Prerequisites
- Python 3.11+ installed (Standard Library only — **no `pip install` required!**)
- Modern web browser

### Step 1: Clone Repository
```bash
git clone https://github.com/Edgywol/Solana_Ecosystem.git
cd solana-ecosystem-dashboard
```

### Step 2: Ingest Live Data & Compile Reports
```bash
python3 run.py
```
*Outputs generated `data/report.json`, `data/report.md`, and updates `data/snapshots.db`.*

### Step 3: Launch Local Dashboard Preview
```bash
python3 -m http.server 8000
```
Open your browser at: **[http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)** (or `http://localhost:8000/`).

---

## 🧪 Running Unit Tests
To verify the anomaly detection engine triggers against synthetic stress scenarios:
```bash
python3 -m collector.anomaly
```

---

## ⚠️ Transparent Limitations & Scope

- **Community Sentiment (real, keyless — Twitter/X proxy):** CoinGecko crowd vote (`sentiment_votes_up_percentage`) + SOL momentum, plus a **keyless RSS cascade** (`collector/social_ingest.py`: Nitter RSS → GitHub SIMD Atom) with sentiment tags. We avoid X Enterprise API (paywalled) and never fabricate — reports `unavailable` if all RSS 403s.
- **Daily Active Addresses (real, modeled):** Live RPC fee-payer sample (`getSignaturesForAddress` → `getTransaction` → unique `accountKeys[0]`) extrapolated to a transparent **lower-bound model** (`daily non-vote txns ÷ 35`, exposed & tunable). Labeled as model — authoritative DAA needs Dune/Flipside.
- **Dune Analytics (cache-first, no key required):** `data/dune_cache.json` holds the last known good snapshot (DEX volume + active addresses) with provenance; live refresh only if `DUNE_API_KEY` set (`collector/dune.py`). No key required to run.
- **Tokenized Equities:** No free, keyless public API found after probing Jupiter/RWA feeds — honestly declared in `coverage.not_collected`; DEX volume is shown as proxy.
- **Live Price Ticker:** Dashboard fetches CoinGecko `simple/price` client-side every 60s (`dashboard/app.js:liveTicker`) — price drops appear in ~1 min while `Generated at` provenance stays honest.
- **Public RPC Rate Limits:** Default is `api.mainnet-beta.solana.com` with exponential backoff + snapshot quarantine (`collector/db.py:quarantine`). Supply `SOLANA_RPC_URL`/`SOLANA_RPC_URLS` for N-of-M consensus.

---

## 📄 Submission Requirements — Mapped

| Requirement | Where | Status |
|---|---|---|
| Public GitHub + README | This repo | ✅ |
| Live demo (higher consideration) | **Vercel** `dashboard-flame-gamma-14.vercel.app` + **Pages** `edgywol.github.io/Solana_Ecosystem` | ✅ |
| Sample JSON + Markdown | [`data/report.json`](data/report.json) · [`data/report.md`](data/report.md) | ✅ |
| Data sources write-up | § Data Sources & Methodology + `SECURITY.md` | ✅ |
| Automation strategy | § Automation Strategy + `.github/workflows/refresh.yml` | ✅ |
| Anomaly detection | § Anomaly Detection Engine + `collector/anomaly.py` | ✅ |
| Setup instructions | § How to Run Locally | ✅ |

## ✅ Submission Verification Checklist

- [x] **Public GitHub Repository:** Clean history, `SECURITY.md`, `DESIGN.md`, no secrets (see `SECURITY.md`).
- [x] **Live Hosted Dashboard:** **Vercel** (auto-deploy on push) + **GitHub Pages** (`deploy-pages@v4`), zero build.
- [x] **Committed Sample Reports:** Verified [`data/report.json`](data/report.json) and [`data/report.md`](data/report.md).
- [x] **Zero Dependencies:** Stdlib-only Python (`urllib`/`sqlite3`) + Chart.js CDN, no `pip`/`npm`.
- [x] **Brand Compliance:** Solana logomark + `#9945FF` → `#14F195` gradient, `Inter` + `JetBrains Mono` tabular numerals.
- [x] **Automated Pipeline:** Cron `0 */6 * * *` + `workflow_dispatch` + push trigger, quarantine, auto-deploy.
- [x] **Anomaly Detection:** Exponential-smoothing trend (σ), composite stress, sentiment correlation, forecast band — with `python -m collector.anomaly` unit tests.

> **For Superteam Earn submission:** <br>
> **Link:** `https://github.com/Edgywol/Solana_Ecosystem` <br>
> **Tweet Link:** (your teammate posts X thread) — add `https://dashboard-flame-gamma-14.vercel.app` with `#Solana #SuperteamCanada`
