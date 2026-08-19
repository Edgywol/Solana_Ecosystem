"""Unit tests for the Anomaly Detection Engine."""

import unittest
from collector.anomaly import AnomalyDetector, detect_anomalies


class TestAnomalyEngine(unittest.TestCase):
    def setUp(self):
        self.detector = AnomalyDetector()
        self.baseline_history = [
            {"tps": 3000.0, "slot_time_ms": 405.0, "sol_price_usd": 178.0, "tvl_usd": 4_900_000_000.0, "timestamp": "2026-08-01T00:00:00Z"},
            {"tps": 3100.0, "slot_time_ms": 410.0, "sol_price_usd": 180.0, "tvl_usd": 4_950_000_000.0, "timestamp": "2026-08-02T00:00:00Z"},
            {"tps": 2900.0, "slot_time_ms": 398.0, "sol_price_usd": 176.0, "tvl_usd": 4_850_000_000.0, "timestamp": "2026-08-03T00:00:00Z"},
        ]
        self.normal_onchain = {
            "performance": {"current_tps": 3050.0, "avg_slot_time_ms": 410.0},
            "validators": {"delinquent_stake_pct": 0.1, "delinquent_validators": 2},
            "health": {"rpc_status": "ok", "is_healthy": True},
        }
        self.normal_market = {
            "price": {"price_usd": 180.0, "change_24h_pct": 2.1},
            "defi": {"tvl_usd": 4_900_000_000.0, "tvl_change_24h_pct": 1.2},
        }

    def test_normal_baseline_produces_zero_alerts(self):
        alerts = self.detector.evaluate(self.normal_onchain, self.normal_market, self.baseline_history)
        self.assertEqual(len(alerts), 0)

    def test_tps_drop_triggers_critical_alert(self):
        onchain = dict(self.normal_onchain)
        onchain["performance"] = {"current_tps": 800.0, "avg_slot_time_ms": 410.0}
        alerts = self.detector.evaluate(onchain, self.normal_market, self.baseline_history)
        self.assertTrue(any("TPS" in a.metric and a.severity == "critical" for a in alerts))

    def test_slot_latency_triggers_anomaly(self):
        # Exponential smoothing: 600ms is far above the 398-410ms trend -> triggers critical
        onchain_warn = dict(self.normal_onchain)
        onchain_warn["performance"] = {"current_tps": 3000.0, "avg_slot_time_ms": 600.0}
        alerts_warn = self.detector.evaluate(onchain_warn, self.normal_market, self.baseline_history)
        self.assertTrue(any("Slot" in a.metric for a in alerts_warn),
                        f"Expected a Slot anomaly for 600ms, got {[a.metric for a in alerts_warn]}")

        # Even more extreme: 820ms -> definitely critical
        onchain_crit = dict(self.normal_onchain)
        onchain_crit["performance"] = {"current_tps": 3000.0, "avg_slot_time_ms": 820.0}
        alerts_crit = self.detector.evaluate(onchain_crit, self.normal_market, self.baseline_history)
        self.assertTrue(any("Slot" in a.metric and a.severity == "critical" for a in alerts_crit),
                        f"Expected critical Slot anomaly for 820ms, got {[(a.metric, a.severity) for a in alerts_crit]}")

    def test_delinquency_spike_triggers_alert(self):
        onchain = dict(self.normal_onchain)
        onchain["validators"] = {"delinquent_stake_pct": 4.5, "delinquent_validators": 38}
        alerts = self.detector.evaluate(onchain, self.normal_market, self.baseline_history)
        self.assertTrue(any("Validator" in a.metric for a in alerts))

    def test_price_shock_triggers_alert(self):
        market = dict(self.normal_market)
        market["price"] = {"price_usd": 250.0, "change_24h_pct": 24.5}
        alerts = self.detector.evaluate(self.normal_onchain, market, self.baseline_history)
        self.assertTrue(any("Price" in a.metric for a in alerts),
                        f"Expected a Price anomaly alert, got {[a.metric for a in alerts]}")

    def test_node_health_degradation_triggers_critical(self):
        onchain = dict(self.normal_onchain)
        onchain["health"] = {"rpc_status": "degraded", "is_healthy": False, "summary": "Node out of sync"}
        alerts = self.detector.evaluate(onchain, self.normal_market, self.baseline_history)
        self.assertTrue(any("Health" in a.metric and a.severity == "critical" for a in alerts))


if __name__ == "__main__":
    unittest.main()
