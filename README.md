# Solana Ecosystem Auto-Updating Report & Interactive Dashboard

> **Superteam Canada Bounty Submission**  
> An automated, zero-dependency, institutional-grade analytics dashboard and auto-updating reporting engine for the Solana ecosystem.

[![Auto Update Ecosystem Data](https://github.com/chmgx81/solana-ecosystem-dashboard/actions/workflows/refresh.yml/badge.svg)](https://github.com/chmgx81/solana-ecosystem-dashboard/actions/workflows/refresh.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Zero External Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-success.svg)](collector/)

---

## 🚀 Live Demo

- **Interactive Dashboard:** [https://chmgx81.github.io/solana-ecosystem-dashboard/](https://chmgx81.github.io/solana-ecosystem-dashboard/)
- **Latest JSON Report:** [`data/report.json`](data/report.json)
- **Latest Markdown Report:** [`data/report.md`](data/report.md)

---

## 📌 Overview

The **Solana Ecosystem Auto-Updating Report & Interactive Dashboard** provides a high-density, real-time visual terminal and automated data compilation pipeline tracking core Solana metrics across on-chain performance, validator decentralization, DeFi/economic velocity, and ecosystem upgrades.

---

## 🏛️ Architecture

```
+-----------------------------------------------------------------------------------+
|                                 DATA INGESTION                                    |
|   +-----------------------+   +-----------------------+   +-------------------+   |
|   |   Solana JSON-RPC     |   |   DeFiLlama Public    |   |   CoinGecko Free  |   |
|   |  (TPS, Slots, Stakes) |   |  (TVL, Stables, DEX)  |   |  (Price, 24h MCap)|   |
|   +-----------+-----------+   +-----------+-----------+   +---------+---------+   |
+---------------|---------------------------|-------------------------|-------------+
                |                           |                         |
                +-------------------> + <---+-------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
|                        COLLECTOR & ANOMALY ENGINE (Python stdlib)                 |
|   1. collector/rpc.py               -> Direct JSON-RPC Client                     |
|   2. collector/onchain_metrics.py   -> Network Health & Stake Concentration       |
|   3. collector/market_data.py       -> Economic Indicators & Real Economic Value  |
|   4. collector/news.py              -> Ecosystem Highlights & Upgrades            |
|   5. collector/anomaly.py           -> Heuristic & Statistical Outlier Engine     |
|   6. collector/db.py                -> SQLite Timeseries Snapshots                |
|   7. collector/report_builder.py    -> Multi-format Generator (JSON + Markdown)   |
+-------------------------------------+---------------------------------------------+
                                      |
                       +--------------+--------------+
                       |                             |
                       v                             v
+-------------------------------+             +-------------------------------------+
|        STORAGE & REPORTS      |             |         FRONTEND INTERACTION        |
|  - data/snapshots.db (SQLite) |             |  - dashboard/index.html (Vanilla)   |
|  - data/report.json           | ----------> |  - dashboard/styles.css (Terminal)  |
|  - data/report.md             |             |  - dashboard/app.js (Chart.js CDN)  |
+-------------------------------+             +-------------------------------------+
                       ^
                       |
+-----------------------------------------------------------------------------------+
|                      AUTOMATION PIPELINE (.github/workflows/refresh.yml)          |
|  - Scheduled cron trigger (every 6h) + workflow_dispatch manual run trigger       |
|  - Zero-dependency execution -> Commits fresh data -> Triggers Pages deploy       |
+-----------------------------------------------------------------------------------+
```

---

## 🌐 Data Sources

1. **Direct Solana JSON-RPC (`https://api.mainnet-beta.solana.com`):**
   - `getHealth`, `getSlot`, `getBlockTime`, `getEpochInfo`, `getRecentPerformanceSamples`, `getVoteAccounts`, `getSupply`
2. **DeFiLlama API (`https://api.llama.fi` / `https://stablecoins.llama.fi`):**
   - Chain TVL, 24h DEX Volume, Stablecoin Market Cap on Solana
3. **CoinGecko API (`https://api.coingecko.com/api/v3`):**
   - Live SOL price, 24h price change %, 24h volume, Market Cap
4. **Curated Upgrades & Technical SIMDs (`collector/news.py`):**
   - Hardcoded, verified upgrade tracker for transparent ecosystem reporting (Alpenglow, SIMD-525, Firedancer, etc.).

---

## ⚙️ How to Run Locally

### Prerequisites
- Python 3.11+ (Standard Library only; **no `pip install` required!**)
- Any modern web browser

### 1. Collect Fresh Data and Generate Reports
```bash
# From repository root
python3 -m collector.run
```

### 2. View the Dashboard Locally
```bash
# Launch a lightweight local server
python3 -m http.server 8000
# Open in your browser: http://localhost:8000/dashboard/
```

---

## 🤖 Automation Strategy

A GitHub Action (`.github/workflows/refresh.yml`) automatically executes the collector pipeline every 6 hours and on manual dispatch. Since all scripts use Python stdlib exclusively, execution completes in seconds with zero build fragility, commits updated snapshot records and reports to `main`, and re-deploys GitHub Pages.

---

## 🚨 Anomaly Detection

The pipeline includes an explainable statistical anomaly detection engine (`collector/anomaly.py`) evaluating:
- **TPS Outliers:** Flags deviation (>30%) from trailing average.
- **Slot Time Degradation:** Flags slot times exceeding 600ms baseline.
- **Validator Delinquency Shocks:** Flags spikes in delinquent validator stake.
- **Market Volatility:** Flags 24h TVL or SOL price swings exceeding 10%.
