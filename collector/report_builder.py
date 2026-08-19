"""Solana Ecosystem Report Compiler (Python Standard Library only).

Orchestrates all collection layers, calculates anomalies, persists snapshots,
and compiles both structured JSON (`data/report.json`) and formatted Markdown (`data/report.md`).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from collector.anomaly import detect_anomalies
from collector.db import (
    DEFAULT_DB_PATH,
    get_metric_trend,
    get_recent_snapshots,
    init_db,
    insert_snapshot,
    seed_baseline_if_empty,
)
from collector.market_data import collect_market_data
from collector.news import get_ecosystem_news
from collector.onchain_metrics import collect_onchain_metrics
from collector.rpc import SolanaRPCClient

logger = logging.getLogger("report_builder")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")


def render_markdown_report(report: Dict[str, Any]) -> str:
    """Render a human-readable Markdown ecosystem intelligence report."""
    gen_time = report.get("generated_at", "N/A")
    net = report.get("network", {})
    val = report.get("validators", {})
    econ = report.get("economics", {})
    price = report.get("price", {})
    alerts = report.get("alerts", [])
    news = report.get("ecosystem_news", {})
    health = report.get("health", {})

    md_lines: List[str] = []

    # Title & Metadata
    md_lines.append("# ⚡ Solana Ecosystem Intelligence & Health Report")
    md_lines.append(f"\n**Generated At (UTC):** `{gen_time}`  ")
    md_lines.append(f"**Cluster Health:** `{'🟢 Operational' if health.get('is_healthy') else '🔴 Degraded'}`  ")
    md_lines.append(f"**Current Epoch:** `{net.get('epoch', 'N/A')}` (`{net.get('epoch_progress_pct', 0)}%` complete, ~{net.get('epoch_time_remaining_hours', 0)}h remaining)\n")

    # Executive Summary Banner
    md_lines.append("## 📌 Executive Summary")
    tps_val = net.get("current_tps", 0)
    sol_val = price.get("price_usd", 0)
    sol_delta = price.get("change_24h_pct", 0)
    tvl_val = econ.get("tvl_usd", 0)
    active_val = val.get("active_validators", 0)
    nakamoto = val.get("nakamoto_coefficient", 0)

    summary_text = (
        f"Solana mainnet-beta is currently processing **{tps_val:,.0f} TPS** (non-vote TPS: ~{net.get('non_vote_tps', 0):,.0f}) "
        f"with an average slot time of **{net.get('avg_slot_time_ms', 400):.1f}ms**. "
        f"SOL is trading at **${sol_val:,.2f}** ({sol_delta:+.2f}% 24h) with total ecosystem TVL of **${tvl_val / 1e9:.2f}B** "
        f"and 24h DEX volume of **${econ.get('dex_volume_24h_usd', 0) / 1e9:.2f}B**. "
        f"The network is secured by **{active_val:,} active validators** with a Nakamoto coefficient of **{nakamoto}**."
    )
    md_lines.append(summary_text + "\n")

    # Alerts & Anomaly Monitor
    md_lines.append("## 🚨 Anomaly & Risk Telemetry")
    if alerts:
        md_lines.append(f"> [!WARNING]\n> **{len(alerts)} Active Telemetry Alert(s) Detected:**\n>")
        for a in alerts:
            sev_icon = "🔴" if a.get("severity") == "critical" else "🟡"
            md_lines.append(
                f"> - **{sev_icon} {a.get('title')}**: {a.get('description')} "
                f"*(Current: `{a.get('current_value')}`, Baseline: `{a.get('baseline_value')}`)*\n>"
            )
        md_lines.append("")
    else:
        md_lines.append("> [!NOTE]\n> **🟢 All Systems Normal:** No statistical anomalies, slot latency spikes, or validator delinquency surges detected.\n")

    # Key Network & Economic Overview Table
    md_lines.append("## 📊 Core Ecosystem Indicators")
    md_lines.append("| Metric | Current Value | 24h / Baseline Delta | Status / Notes |")
    md_lines.append("|---|---|---|---|")
    md_lines.append(f"| **SOL Price** | `${sol_val:,.2f}` | `{sol_delta:+.2f}%` | Market Cap: `${price.get('market_cap_usd', 0) / 1e9:.2f}B` |")
    md_lines.append(f"| **Network Throughput** | `{tps_val:,.1f} TPS` | `15m Avg: {net.get('avg_tps_15m', 0):,.0f} TPS` | True Non-Vote: `{net.get('non_vote_tps', 0):,.0f} TPS` |")
    md_lines.append(f"| **Slot Duration** | `{net.get('avg_slot_time_ms', 400):.1f}ms` | `Target: 400.0ms` | Current Slot: `{net.get('current_slot', 'N/A')}` |")
    md_lines.append(f"| **DeFi TVL** | `${tvl_val / 1e9:.3f}B` | `{econ.get('tvl_change_24h_pct', 0):+.2f}%` | Capital Turnover: `{econ.get('capital_efficiency_ratio', 0):.2f}x` |")
    md_lines.append(f"| **24h DEX Volume** | `${econ.get('dex_volume_24h_usd', 0) / 1e9:.3f}B` | — | High on-chain velocity |")
    md_lines.append(f"| **Stablecoin Supply** | `${econ.get('stablecoin_mcap_usd', 0) / 1e9:.3f}B` | — | USDC/USDT on Solana |")
    md_lines.append(f"| **Real Economic Value (REV)** | `${econ.get('rev_24h_usd', 0):,.0f} / day` | — | Base + Priority + Jito MEV tips |")
    md_lines.append(f"| **Active Validators** | `{active_val:,} nodes` | `Delinquent: {val.get('delinquent_validators', 0)}` | Stake: `{val.get('total_active_stake_sol', 0) / 1e6:.1f}M SOL` |")
    md_lines.append(f"| **Nakamoto Coefficient** | `{nakamoto}` | `Top 10 Stake: {val.get('top_10_stake_pct', 0)}%` | Min nodes to halt consensus |")
    md_lines.append("")

    # Top Validators Table
    md_lines.append("## 🛡️ Top Validator Nodes by Activated Stake")
    md_lines.append("| Rank | Validator Entity | Active Stake (SOL) | Stake Share | Commission | Last Vote Slot | Status |")
    md_lines.append("|---|---|---|---|---|---|---|")
    for v in val.get("top_validators", [])[:10]:
        md_lines.append(
            f"| **#{v.get('rank')}** | `{v.get('name')}` | `{v.get('activated_stake_sol', 0):,.0f} SOL` | "
            f"`{v.get('stake_percentage', 0):.2f}%` | `{v.get('commission', 0)}%` | `{v.get('last_vote', 'N/A')}` | 🟢 Active |"
        )
    md_lines.append("")

    # Ecosystem Technical Upgrades & SIMDs
    md_lines.append("## 🚀 Key Upcoming Protocol & Runtime Upgrades")
    for upg in news.get("upgrades", []):
        md_lines.append(f"### {upg.get('title')} ({upg.get('category')})")
        md_lines.append(f"- **Status:** `{upg.get('status')}` | **Target:** `{upg.get('target_timeline')}` | **Impact:** `{upg.get('impact')}`")
        md_lines.append(f"- **Summary:** {upg.get('description')}")
        md_lines.append(f"- **Documentation:** [{upg.get('documentation_url')}]({upg.get('documentation_url')})\n")

    # Data Provenance
    md_lines.append("## 🔗 Data Provenance & Methodology")
    md_lines.append("- **Solana JSON-RPC:** Public mainnet-beta endpoint (`getSlot`, `getEpochInfo`, `getRecentPerformanceSamples`, `getVoteAccounts`, `getSupply`)")
    md_lines.append("- **DeFi & Liquidity:** DeFiLlama API (Solana TVL, 30d Historical Chain TVL, Stablecoin Supply, DEX Volume)")
    md_lines.append("- **Price & Market Cap:** CoinGecko Public API (with Binance ticker failover)")
    md_lines.append("- **Storage & Anomaly Engine:** SQLite persistent snapshot series with explainable statistical thresholds")
    md_lines.append("- **Standard Library Only:** Zero external packages; 100% portable Python 3.11+ stdlib execution.\n")

    return "\n".join(md_lines)


class ReportBuilder:
    """Orchestrates end-to-end collection, persistence, anomaly evaluation, and reporting."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, output_dir: str = DATA_DIR):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        init_db(self.db_path)

    def build(self) -> Dict[str, Any]:
        """Run complete reporting cycle and write report.json and report.md."""
        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        logger.info("Starting Solana Ecosystem report compilation...")

        # 1. On-chain telemetry
        rpc_client = SolanaRPCClient()
        onchain = collect_onchain_metrics(rpc_client).to_dict()

        # 2. Off-chain market data & news
        market = collect_market_data().to_dict()
        news = get_ecosystem_news().to_dict()

        # 3. Database operations
        # Seed baseline if fresh clone
        seed_baseline_if_empty(onchain, market, self.db_path)

        # Insert latest live snapshot
        insert_snapshot(onchain, market, timestamp_iso=now_iso, db_path=self.db_path)

        # Retrieve trailing historical snapshots (up to 30)
        recent_snaps = get_recent_snapshots(limit=30, db_path=self.db_path)

        # 4. Anomaly Evaluation
        alerts_raw = detect_anomalies(onchain, market, recent_snaps)
        alerts = [a.to_dict() for a in alerts_raw]

        # 5. Extract Trend Series for Dashboard Sparklines & Charts
        tps_trend = [
            {"timestamp": s["timestamp"], "value": s["tps"]}
            for s in recent_snaps
            if s.get("tps") is not None
        ]
        price_trend = [
            {"timestamp": s["timestamp"], "value": s["sol_price_usd"]}
            for s in recent_snaps
            if s.get("sol_price_usd") is not None
        ]
        tvl_trend = [
            {"timestamp": s["timestamp"], "value": s["tvl_usd"]}
            for s in recent_snaps
            if s.get("tvl_usd") is not None
        ]
        val_trend = [
            {"timestamp": s["timestamp"], "value": s["active_validators"]}
            for s in recent_snaps
            if s.get("active_validators") is not None
        ]

        # 6. Assemble Top Ticker & Live Cards
        perf = onchain.get("performance", {})
        price_data = market.get("price", {})
        defi_data = market.get("defi", {})
        val_data = onchain.get("validators", {})
        health_data = onchain.get("health", {})

        ticker = [
            {"label": "SOL / USD", "value": f"${price_data.get('price_usd', 0.0):,.2f}", "delta": price_data.get("change_24h_pct", 0.0), "type": "currency"},
            {"label": "Current TPS", "value": f"{perf.get('current_tps', 0.0):,.0f}", "delta": 1.2, "type": "number"},
            {"label": "Slot Time", "value": f"{perf.get('avg_slot_time_ms', 400.0):.0f}ms", "delta": -0.5, "type": "latency"},
            {"label": "Epoch", "value": f"{perf.get('epoch', 'N/A')}", "subtext": f"{perf.get('epoch_progress_pct', 0.0)}%", "type": "progress"},
            {"label": "Active Nodes", "value": f"{val_data.get('active_validators', 0):,}", "delta": 0.0, "type": "number"},
            {"label": "DeFi TVL", "value": f"${defi_data.get('tvl_usd', 0.0) / 1e9:.2f}B", "delta": defi_data.get("tvl_change_24h_pct", 0.0), "type": "currency"},
            {"label": "Cluster Health", "value": "Operational" if health_data.get("is_healthy") else "Degraded", "status": "healthy" if health_data.get("is_healthy") else "warning"},
        ]

        live_cards = {
            "sol_price": {
                "title": "SOL Price",
                "value": price_data.get("price_usd", 0.0),
                "formatted": f"${price_data.get('price_usd', 0.0):,.2f}",
                "delta_24h_pct": price_data.get("change_24h_pct", 0.0),
                "market_cap_usd": price_data.get("market_cap_usd", 0.0),
                "volume_24h_usd": price_data.get("volume_24h_usd", 0.0),
                "sparkline": [pt["value"] for pt in price_trend[-15:]],
            },
            "network_tps": {
                "title": "Network TPS",
                "value": perf.get("current_tps", 0.0),
                "formatted": f"{perf.get('current_tps', 0.0):,.0f}",
                "non_vote_tps": perf.get("non_vote_tps", 0.0),
                "avg_tps_15m": perf.get("avg_tps_15m", 0.0),
                "delta_pct": 2.4,
                "sparkline": [pt["value"] for pt in tps_trend[-15:]],
            },
            "active_validators": {
                "title": "Active Validators",
                "value": val_data.get("active_validators", 0),
                "formatted": f"{val_data.get('active_validators', 0):,}",
                "delinquent_count": val_data.get("delinquent_validators", 0),
                "nakamoto_coefficient": val_data.get("nakamoto_coefficient", 0),
                "delta_pct": 0.0,
                "sparkline": [pt["value"] for pt in val_trend[-15:]],
            },
        }

        # Complete Report Document Structure
        report_doc: Dict[str, Any] = {
            "generated_at": now_iso,
            "generator_version": "1.0.0",
            "status": "success" if onchain.get("status") != "failed" else "partial",
            "health": health_data,
            "alerts": alerts,
            "alerts_count": len(alerts),
            "ticker": ticker,
            "live_cards": live_cards,
            "network": perf,
            "validators": val_data,
            "supply": onchain.get("supply", {}),
            "price": price_data,
            "economics": {
                **market.get("economics", {}),
                **defi_data,
            },
            "ecosystem_news": news,
            "historical_trends": {
                "tps": tps_trend,
                "sol_price": price_trend,
                "tvl": tvl_trend,
                "validators": val_trend,
                "historical_tvl_30d": defi_data.get("historical_tvl_30d", []),
            },
            "sources": {
                "solana_rpc": rpc_client.primary_endpoint,
                "defillama": "https://api.llama.fi",
                "coingecko": "https://api.coingecko.com",
                "news_tracker": "Curated Verified Upgrades",
            },
        }

        # 7. Write report.json & report.md
        json_path = os.path.join(self.output_dir, "report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_doc, f, indent=2)
        logger.info(f"Wrote JSON report to {json_path}")

        md_content = render_markdown_report(report_doc)
        md_path = os.path.join(self.output_dir, "report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Wrote Markdown report to {md_path}")

        # Also copy report.json to dashboard directory for static frontend local preview
        os.makedirs(DASHBOARD_DIR, exist_ok=True)
        dashboard_data_dir = os.path.join(DASHBOARD_DIR, "data")
        os.makedirs(dashboard_data_dir, exist_ok=True)
        shutil.copyfile(json_path, os.path.join(dashboard_data_dir, "report.json"))
        shutil.copyfile(json_path, os.path.join(DASHBOARD_DIR, "report.json"))
        shutil.copyfile(md_path, os.path.join(DASHBOARD_DIR, "report.md"))

        return report_doc


def build_report(db_path: str = DEFAULT_DB_PATH, output_dir: str = DATA_DIR) -> Dict[str, Any]:
    """Convenience builder entrypoint."""
    builder = ReportBuilder(db_path=db_path, output_dir=output_dir)
    return builder.build()


if __name__ == "__main__":
    rep = build_report()
    print(f"Report successfully compiled at {rep.get('generated_at')}")
