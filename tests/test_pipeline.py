"""Integration tests for SQLite persistence, report compiler, and schema integrity."""

import json
import os
import tempfile
import unittest
from collector.db import init_db, insert_snapshot, get_recent_snapshots, get_metric_trend
from collector.news import get_ecosystem_news
from collector.report_builder import render_markdown_report


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_snapshots.db")
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_insertion_and_retrieval(self):
        onchain = {
            "performance": {"epoch": 1018, "current_slot": 440180000, "current_tps": 3500.0, "non_vote_tps": 2000.0, "avg_slot_time_ms": 412.0},
            "validators": {"active_validators": 687, "delinquent_validators": 8, "total_active_stake_sol": 435000000.0, "nakamoto_coefficient": 18},
        }
        market = {
            "price": {"price_usd": 180.5, "change_24h_pct": 3.5},
            "defi": {"tvl_usd": 4900000000.0, "dex_volume_24h_usd": 1800000000.0, "stablecoin_mcap_usd": 15000000000.0},
            "economics": {"rev_24h_usd": 750000.0},
        }

        row_id = insert_snapshot(onchain, market, db_path=self.db_path)
        self.assertGreater(row_id, 0)

        snaps = get_recent_snapshots(10, db_path=self.db_path)
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["epoch"], 1018)
        self.assertEqual(snaps[0]["tps"], 3500.0)
        self.assertEqual(snaps[0]["sol_price_usd"], 180.5)

        trend = get_metric_trend("tps", db_path=self.db_path)
        self.assertEqual(len(trend), 1)
        self.assertEqual(trend[0]["value"], 3500.0)

    def test_news_tracker_returns_valid_structure(self):
        news = get_ecosystem_news()
        self.assertGreater(len(news.upgrades), 0)
        self.assertTrue(any("Alpenglow" in u.title for u in news.upgrades))
        self.assertTrue(any("Firedancer" in u.title for u in news.upgrades))

    def test_markdown_report_rendering(self):
        mock_report = {
            "generated_at": "2026-08-19T00:00:00Z",
            "health": {"is_healthy": True, "cluster_status": "Operational"},
            "network": {"epoch": 1018, "epoch_progress_pct": 93.2, "epoch_time_remaining_hours": 3.4, "current_tps": 3800.0, "non_vote_tps": 2100.0, "avg_slot_time_ms": 415.0, "current_slot": 440180000, "avg_tps_15m": 4000.0},
            "validators": {"active_validators": 687, "delinquent_validators": 8, "total_active_stake_sol": 435000000.0, "nakamoto_coefficient": 18, "top_10_stake_pct": 24.4, "top_validators": []},
            "economics": {"tvl_usd": 4900000000.0, "tvl_change_24h_pct": 0.65, "dex_volume_24h_usd": 1800000000.0, "stablecoin_mcap_usd": 15000000000.0, "rev_24h_usd": 750000.0, "capital_efficiency_ratio": 0.37},
            "price": {"price_usd": 180.0, "change_24h_pct": 1.8, "market_cap_usd": 45000000000.0},
            "alerts": [],
            "ecosystem_news": {"upgrades": []}
        }
        md = render_markdown_report(mock_report)
        self.assertIn("Solana Ecosystem Intelligence", md)
        self.assertIn("Executive Summary", md)
        self.assertIn("Core Ecosystem Indicators", md)


if __name__ == "__main__":
    unittest.main()
