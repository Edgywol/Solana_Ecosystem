#!/usr/bin/env python3
"""Solana Ecosystem Auto-Updating Report & Dashboard Orchestrator.

Single entrypoint executing the complete data pipeline:
1. Ingests on-chain metrics via Solana JSON-RPC
2. Ingests off-chain metrics from DeFiLlama and CoinGecko
3. Persists historical timeseries snapshot to SQLite (data/snapshots.db)
4. Evaluates explainable anomaly alerts (collector/anomaly.py)
5. Compiles JSON report (data/report.json) & Markdown report (data/report.md)
6. Synchronizes static assets for GitHub Pages dashboard
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from collector.report_builder import ReportBuilder


def print_banner(report: dict, elapsed_sec: float) -> None:
    """Print terminal summary banner."""
    net = report.get("network", {})
    val = report.get("validators", {})
    price = report.get("price", {})
    econ = report.get("economics", {})
    alerts = report.get("alerts", [])
    health = report.get("health", {})

    term_width = 80
    border = "=" * term_width
    sub_border = "-" * term_width

    print("\n" + border)
    print("  ⚡ SOLANA ECOSYSTEM AUTO-UPDATING REPORT & DASHBOARD ENGINE ⚡")
    print(f"  Generated: {report.get('generated_at')} | Pipeline Time: {elapsed_sec:.2f}s")
    print(border)

    status_icon = "🟢" if health.get("is_healthy") else "🔴"
    print(f"  Cluster Health: {status_icon} {health.get('cluster_status', 'N/A')} (RPC: {health.get('rpc_status', 'N/A')})")
    print(f"  Active Alerts:  {len(alerts)} active telemetry anomaly alert(s)")
    print(sub_border)

    # Core Metrics Grid
    print("  📊 TELEMETRY HIGHLIGHTS:")
    print(f"  • SOL Price:           ${price.get('price_usd', 0.0):,.2f} ({price.get('change_24h_pct', 0.0):+.2f}% 24h)")
    print(f"  • Network TPS:         {net.get('current_tps', 0.0):,.1f} TPS (Non-vote: {net.get('non_vote_tps', 0.0):,.1f} TPS)")
    print(f"  • Avg Slot Time:       {net.get('avg_slot_time_ms', 400.0):.1f} ms (Current Slot: {net.get('current_slot', 'N/A')})")
    print(f"  • Epoch Progress:      Epoch {net.get('epoch', 'N/A')} [{net.get('epoch_progress_pct', 0.0)}% complete, ~{net.get('epoch_time_remaining_hours', 0.0)}h remaining]")
    print(f"  • Active Validators:   {val.get('active_validators', 0):,} nodes (Nakamoto Coeff: {val.get('nakamoto_coefficient', 0)})")
    print(f"  • Total Active Stake:  {val.get('total_active_stake_sol', 0.0) / 1e6:,.2f}M SOL ({val.get('delinquent_stake_pct', 0.0)}% delinquent)")
    print(f"  • DeFi TVL:            ${econ.get('tvl_usd', 0.0) / 1e9:.3f}B ({econ.get('tvl_change_24h_pct', 0.0):+.2f}% 24h)")
    print(f"  • 24h DEX Volume:      ${econ.get('dex_volume_24h_usd', 0.0) / 1e9:.3f}B")
    print(f"  • Stablecoins MCap:    ${econ.get('stablecoin_mcap_usd', 0.0) / 1e9:.3f}B")
    print(f"  • Real Economic Value: ${econ.get('rev_24h_usd', 0.0):,.2f} / day (Proxy estimate)")
    print(sub_border)

    # Active alerts if any
    if alerts:
        print("  🚨 ACTIVE ANOMALIES:")
        for a in alerts:
            icon = "🔴" if a.get("severity") == "critical" else "🟡"
            print(f"    {icon} [{a.get('severity').upper()}] {a.get('title')}: {a.get('description')}")
        print(sub_border)

    # Generated files
    print("  📁 OUTPUT ARTIFACTS WRITTEN:")
    print(f"  ✓ JSON Report:      {os.path.join(BASE_DIR, 'data', 'report.json')}")
    print(f"  ✓ Markdown Report:  {os.path.join(BASE_DIR, 'data', 'report.md')}")
    print(f"  ✓ SQLite Snapshot:  {os.path.join(BASE_DIR, 'data', 'snapshots.db')}")
    print(f"  ✓ Static Dashboard: {os.path.join(BASE_DIR, 'dashboard', 'data', 'report.json')}")
    print(border + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Solana Ecosystem Report Collector")
    parser.add_argument("--db-path", default=None, help="Custom SQLite DB path")
    parser.add_argument("--output-dir", default=None, help="Custom report output directory")
    args = parser.parse_args()

    start_time = time.time()
    db_path = args.db_path or os.path.join(BASE_DIR, "data", "snapshots.db")
    output_dir = args.output_dir or os.path.join(BASE_DIR, "data")

    try:
        builder = ReportBuilder(db_path=db_path, output_dir=output_dir)
        report = builder.build()
        elapsed = time.time() - start_time

        print_banner(report, elapsed)

        # Check critical conditions for return code
        if report.get("status") == "failed":
            print("ERROR: Report generation status was 'failed'.", file=sys.stderr)
            return 1

        return 0

    except Exception as e:
        print(f"FATAL ERROR during report compilation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
