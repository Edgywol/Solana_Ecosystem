# ⚡ Solana Ecosystem Auto-Updating Intelligence Report & Interactive Terminal

> **Superteam Canada Bounty Submission:** Develop Solana Ecosystem Auto-Updating Report & Interactive Dashboard  
> **Repository:** [https://github.com/chmgx81/solana-ecosystem-dashboard](https://github.com/chmgx81/solana-ecosystem-dashboard)  
> **Live Interactive Terminal:** [https://chmgx81.github.io/solana-ecosystem-dashboard/](https://chmgx81.github.io/solana-ecosystem-dashboard/)  
> **Generated JSON Feed:** [`data/report.json`](data/report.json)  
> **Generated Markdown Report:** [`data/report.md`](data/report.md)  
> **License:** MIT (Open Source)

---

## 🌟 Submission Highlights & Key Differentiators

- **Zero External Dependencies:** Built with **Python 3.11+ Standard Library only** (`urllib`, `json`, `sqlite3`, `datetime`, `dataclasses`). **No `pip install`, no node_modules, no API keys needed.**
- **Direct On-Chain Telemetry:** JSON-RPC client directly against Solana mainnet-beta with automatic gzip decompression and multi-endpoint failover.
- **Explainable Anomaly & Risk Engine:** Statistically evaluates current telemetry against trailing SQLite baselines to detect TPS shocks, slot latency delays, validator delinquency jumps, and TVL drawdowns.
- **Institutional Fintech UX:** Trading-terminal density, persistent left sidebar, live ticker strip, Chart.js embedded sparklines, and responsive mobile-first architecture.
- **Complete Automation Loop:** Scheduled GitHub Action (`refresh.yml`) running every 6 hours and on-demand via `workflow_dispatch`, committing refreshed snapshots and auto-deploying to GitHub Pages.

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------------------------------+
|                                      DATA INGESTION LAYER                                     |
|                                                                                               |
|   +-----------------------------+   +---------------------------+   +---------------------+   |
|   |      Solana JSON-RPC        |   |      DeFiLlama Public     |   |    CoinGecko Free   |   |
|   |  (TPS, Slots, Stakes, Node) |   |    (TVL, 30d Hist, DEX)   |   |  (Spot Price, 24h)  |   |
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
|   5. collector/anomaly.py           -> Heuristic statistical anomaly detection engine         |
|   6. collector/db.py                -> SQLite persistent timeseries snapshot storage          |
|   7. collector/report_builder.py    -> Dual-format report compiler (JSON + Markdown)          |
+---------------------------------------------+-------------------------------------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
+---------------------------------------------+   +---------------------------------------------+
|               STORAGE & FEEDS               |   |            INTERACTIVE DASHBOARD            |
|                                             |   |                                             |
|   - data/snapshots.db (SQLite Timeseries)   |   |   - dashboard/index.html (Vanilla UI)       |
|   - data/report.json  (Machine-Readable)    |-->|   - dashboard/styles.css (Dark Terminal UX) |
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
| **Protocol Roadmap** | Hand-Curated Technical Ledger | `collector/news.py` | Curated technical upgrade ledger covering Alpenglow, Firedancer, SIMD-0096, and SIMD-0123. |

---

## 🚨 Anomaly Detection Engine

The anomaly detection engine (`collector/anomaly.py`) uses explainable, deterministic statistical checks against historical snapshots:

```python
# Core Anomaly Rules Evaluated on Every Run:
1. TPS Shock: Flags if current TPS deviates >30% (Warning) or >60% (Critical) from trailing 7-day average.
2. Slot Duration: Flags if average slot time exceeds 550ms (Warning) or 750ms (Critical) against 400ms target.
3. Delinquency Spike: Flags if delinquent validator stake exceeds 2.0% of total active stake.
4. Market Volatility: Flags if 24h SOL price moves >10% (Warning) or >20% (Critical).
5. TVL Drawdown: Flags if 24h DeFi TVL drops >10%.
6. Cluster Health: Flags if RPC health status is degraded or node connectivity fails.
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
git clone https://github.com/chmgx81/solana-ecosystem-dashboard.git
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

- **X/Twitter Sentiment:** Due to enterprise API paywalls on X/Twitter, social scraping is replaced with a verified, hand-curated technical upgrade tracker (`collector/news.py`).
- **Dune Analytics:** Dune is treated as optional/best-effort to prevent rate-limiting dependencies on third-party API keys; all core on-chain data is obtained directly from native Solana JSON-RPC endpoints.
- **Public RPC Rate Limits:** The collector includes multi-endpoint fallback logic (`api.mainnet-beta.solana.com`, `rpc.ankr.com`, `solana.drpc.org`). For high-frequency enterprise querying, custom RPC endpoints can be supplied via `SOLANA_RPC_URL`.

---

## 📄 Submission Verification Checklist

- [x] **Public GitHub Repository:** Clean git commit history and structured modules.
- [x] **Live Hosted Dashboard:** Fully functional on GitHub Pages with zero frontend build requirements.
- [x] **Committed Sample Reports:** Verified [`data/report.json`](data/report.json) and [`data/report.md`](data/report.md).
- [x] **Zero Dependencies:** Pure Python standard library implementation.
- [x] **Brand Compliance:** Official Solana SVG logomark and `#9945FF` -> `#14F195` color palette.
- [x] **Automated Pipeline:** Scheduled GitHub Action with cron and manual dispatch.
- [x] **Anomaly Detection:** Explainable rule-based outlier monitoring with synthetic unit tests.
