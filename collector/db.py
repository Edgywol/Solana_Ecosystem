"""SQLite Storage Layer for Solana Ecosystem Snapshots (Python Standard Library only).

Provides persistent timeseries storage for network metrics, market metrics,
and historical trend analysis.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("db")

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "snapshots.db")


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize the SQLite database schema if not already present."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                epoch INTEGER,
                slot INTEGER,
                tps REAL,
                non_vote_tps REAL,
                avg_slot_time_ms REAL,
                active_validators INTEGER,
                delinquent_validators INTEGER,
                total_active_stake_sol REAL,
                nakamoto_coefficient INTEGER,
                sol_price_usd REAL,
                sol_24h_change_pct REAL,
                tvl_usd REAL,
                dex_volume_24h_usd REAL,
                stablecoin_mcap_usd REAL,
                rev_24h_usd REAL,
                raw_metrics_json TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_epoch ON snapshots(epoch)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_slot ON snapshots(slot)")
        conn.commit()


def insert_snapshot(
    onchain: Dict[str, Any],
    market: Dict[str, Any],
    timestamp_iso: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Insert a single snapshot row and return the inserted row ID."""
    init_db(db_path)
    ts = timestamp_iso or datetime.now(timezone.utc).isoformat()

    perf = onchain.get("performance", {})
    val = onchain.get("validators", {})
    price = market.get("price", {})
    defi = market.get("defi", {})
    econ = market.get("economics", {})

    combined_blob = json.dumps({"onchain": onchain, "market": market})

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO snapshots (
                timestamp, epoch, slot, tps, non_vote_tps, avg_slot_time_ms,
                active_validators, delinquent_validators, total_active_stake_sol,
                nakamoto_coefficient, sol_price_usd, sol_24h_change_pct,
                tvl_usd, dex_volume_24h_usd, stablecoin_mcap_usd, rev_24h_usd,
                raw_metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                perf.get("epoch"),
                perf.get("current_slot"),
                perf.get("current_tps", 0.0),
                perf.get("non_vote_tps", 0.0),
                perf.get("avg_slot_time_ms", 400.0),
                val.get("active_validators", 0),
                val.get("delinquent_validators", 0),
                val.get("total_active_stake_sol", 0.0),
                val.get("nakamoto_coefficient", 0),
                price.get("price_usd", 0.0),
                price.get("change_24h_pct", 0.0),
                defi.get("tvl_usd", 0.0),
                defi.get("dex_volume_24h_usd", 0.0),
                defi.get("stablecoin_mcap_usd", 0.0),
                econ.get("rev_24h_usd", 0.0),
                combined_blob,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0


def get_recent_snapshots(limit: int = 30, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetch the last N snapshots ordered from oldest to newest for charting."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM (
                SELECT * FROM snapshots ORDER BY id DESC LIMIT ?
            ) sub ORDER BY id ASC
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_metric_trend(metric_name: str, limit: int = 30, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve timestamp and metric value pairs for trend sparklines."""
    snapshots = get_recent_snapshots(limit, db_path)
    return [
        {
            "timestamp": s.get("timestamp"),
            "value": s.get(metric_name),
        }
        for s in snapshots
        if s.get(metric_name) is not None
    ]


def seed_baseline_if_empty(
    current_onchain: Dict[str, Any],
    current_market: Dict[str, Any],
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Seed historical trailing snapshots if database has fewer than 7 entries.
    
    Uses historical DeFiLlama daily TVL data points and proportional network variance
    to ensure new clones immediately have robust sparklines and trailing 7-day anomaly baselines.
    """
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM snapshots")
        count = cursor.fetchone()[0]

    if count >= 7:
        return

    logger.info(f"Database has {count} snapshots; generating 14-day trailing baseline...")
    hist_tvl = current_market.get("defi", {}).get("historical_tvl_30d", [])
    now = datetime.now(timezone.utc)

    # Base values
    base_tps = current_onchain.get("performance", {}).get("current_tps", 3200.0)
    base_price = current_market.get("price", {}).get("price_usd", 180.0)
    base_val = current_onchain.get("validators", {}).get("active_validators", 680)
    base_stake = current_onchain.get("validators", {}).get("total_active_stake_sol", 435000000.0)
    base_slot = current_onchain.get("performance", {}).get("current_slot", 440000000) or 440000000

    # Create 14 trailing data points (spaced 1 day apart)
    for i in range(14, 0, -1):
        pt_time = now - timedelta(days=i)
        tvl_val = (
            hist_tvl[-i]["tvl"]
            if len(hist_tvl) >= i
            else current_market.get("defi", {}).get("tvl_usd", 4800000000.0)
        )
        # Moderate realistic variance for historical trend simulation
        tps_var = base_tps * (0.92 + (i % 5) * 0.03)
        price_var = base_price * (0.95 + (i % 7) * 0.015)
        slot_var = base_slot - (i * 200000)

        mock_onchain = dict(current_onchain)
        mock_onchain["performance"] = dict(current_onchain.get("performance", {}))
        mock_onchain["performance"]["current_tps"] = round(tps_var, 1)
        mock_onchain["performance"]["current_slot"] = slot_var

        mock_market = dict(current_market)
        mock_market["price"] = dict(current_market.get("price", {}))
        mock_market["price"]["price_usd"] = round(price_var, 2)
        mock_market["defi"] = dict(current_market.get("defi", {}))
        mock_market["defi"]["tvl_usd"] = round(tvl_val, 2)

        insert_snapshot(mock_onchain, mock_market, timestamp_iso=pt_time.isoformat(), db_path=db_path)

    logger.info("Baseline snapshots successfully seeded.")


if __name__ == "__main__":
    init_db()
    snaps = get_recent_snapshots(5)
    print(f"Snapshot table initialized. Current row count: {len(snaps)}")
