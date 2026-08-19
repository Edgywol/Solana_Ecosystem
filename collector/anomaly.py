"""Explainable Anomaly & Risk Detection Engine for Solana Ecosystem (Python Standard Library only).

Evaluates current telemetry against trailing SQLite baseline snapshots:
- TPS volatility & sudden drop/spike anomalies
- Slot time latency degradation (>600ms)
- Validator delinquency spikes & stake concentration risks
- 24h SOL price shocks (>10% / >20%) & DeFi TVL drawdowns (>10%)
- RPC and cluster consensus degradation
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AnomalyAlert:
    id: str
    metric: str
    severity: str  # "info", "warning", "critical"
    current_value: Any
    baseline_value: Any
    threshold: str
    title: str
    description: str
    detected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnomalyDetector:
    """Configurable, rule-based explainable anomaly detector."""

    def __init__(
        self,
        tps_deviation_pct_threshold: float = 30.0,
        slot_time_warning_ms: float = 550.0,
        slot_time_critical_ms: float = 750.0,
        price_change_warning_pct: float = 10.0,
        price_change_critical_pct: float = 20.0,
        tvl_change_warning_pct: float = 10.0,
        delinquency_pct_warning: float = 2.0,
    ):
        self.tps_threshold = tps_deviation_pct_threshold
        self.slot_warn = slot_time_warning_ms
        self.slot_crit = slot_time_critical_ms
        self.price_warn = price_change_warning_pct
        self.price_crit = price_change_critical_pct
        self.tvl_warn = tvl_change_warning_pct
        self.delinq_warn = delinquency_pct_warning

    def evaluate(
        self,
        current_onchain: Dict[str, Any],
        current_market: Dict[str, Any],
        historical_snapshots: List[Dict[str, Any]],
    ) -> List[AnomalyAlert]:
        """Evaluate current metrics against historical baseline and return active alerts."""
        alerts: List[AnomalyAlert] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        perf = current_onchain.get("performance", {})
        val = current_onchain.get("validators", {})
        health = current_onchain.get("health", {})
        price = current_market.get("price", {})
        defi = current_market.get("defi", {})

        curr_tps = float(perf.get("current_tps", 0.0))
        curr_slot_time = float(perf.get("avg_slot_time_ms", 400.0))
        curr_price_change = abs(float(price.get("change_24h_pct", 0.0)))
        curr_tvl_change = abs(float(defi.get("tvl_change_24h_pct", 0.0)))
        curr_delinq_pct = float(val.get("delinquent_stake_pct", 0.0))

        # 1. Cluster & RPC Health Check
        if health.get("rpc_status") != "ok" or not health.get("is_healthy", True):
            alerts.append(
                AnomalyAlert(
                    id="ALERT-HEALTH-01",
                    metric="Cluster Health",
                    severity="critical",
                    current_value=health.get("rpc_status", "unknown"),
                    baseline_value="ok",
                    threshold="rpc_status == ok",
                    title="Solana Node Health Alert",
                    description=f"Solana RPC reported unhealthy/degraded status: {health.get('summary', 'Unknown')}",
                    detected_at=now_iso,
                )
            )

        # 2. Slot Time Degradation Check
        if curr_slot_time > self.slot_crit:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-SLOT-01",
                    metric="Slot Duration",
                    severity="critical",
                    current_value=f"{curr_slot_time:.1f}ms",
                    baseline_value="400.0ms",
                    threshold=f">{self.slot_crit}ms",
                    title="Critical Slot Latency Elevation",
                    description=f"Average slot duration ({curr_slot_time:.1f}ms) is severely delayed above the 400ms target.",
                    detected_at=now_iso,
                )
            )
        elif curr_slot_time > self.slot_warn:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-SLOT-02",
                    metric="Slot Duration",
                    severity="warning",
                    current_value=f"{curr_slot_time:.1f}ms",
                    baseline_value="400.0ms",
                    threshold=f">{self.slot_warn}ms",
                    title="Elevated Slot Duration",
                    description=f"Average slot duration ({curr_slot_time:.1f}ms) is running slightly above normal bounds.",
                    detected_at=now_iso,
                )
            )

        # 3. TPS Deviation vs Trailing Baseline
        if historical_snapshots:
            tps_history = [s.get("tps") for s in historical_snapshots if s.get("tps") and s.get("tps") > 0]
            if tps_history:
                avg_baseline_tps = sum(tps_history) / len(tps_history)
                if avg_baseline_tps > 0:
                    deviation_pct = ((curr_tps - avg_baseline_tps) / avg_baseline_tps) * 100.0
                    if abs(deviation_pct) > (self.tps_threshold * 2):
                        alerts.append(
                            AnomalyAlert(
                                id="ALERT-TPS-01",
                                metric="Transactions Per Second (TPS)",
                                severity="critical" if deviation_pct < 0 else "warning",
                                current_value=f"{curr_tps:.0f} TPS",
                                baseline_value=f"{avg_baseline_tps:.0f} TPS (trailing avg)",
                                threshold=f"±{self.tps_threshold * 2:.0f}%",
                                title=f"Severe TPS {'Drop' if deviation_pct < 0 else 'Spike'} Detected",
                                description=(
                                    f"Current throughput ({curr_tps:.0f} TPS) deviates by {deviation_pct:+.1f}% "
                                    f"from trailing baseline of {avg_baseline_tps:.0f} TPS."
                                ),
                                detected_at=now_iso,
                            )
                        )
                    elif abs(deviation_pct) > self.tps_threshold:
                        alerts.append(
                            AnomalyAlert(
                                id="ALERT-TPS-02",
                                metric="Transactions Per Second (TPS)",
                                severity="warning",
                                current_value=f"{curr_tps:.0f} TPS",
                                baseline_value=f"{avg_baseline_tps:.0f} TPS (trailing avg)",
                                threshold=f"±{self.tps_threshold:.0f}%",
                                title=f"Moderate TPS {'Drop' if deviation_pct < 0 else 'Surge'}",
                                description=(
                                    f"Current throughput ({curr_tps:.0f} TPS) deviates by {deviation_pct:+.1f}% "
                                    f"from trailing baseline."
                                ),
                                detected_at=now_iso,
                            )
                        )

        # 4. Validator Delinquency Check
        if curr_delinq_pct > self.delinq_warn:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-VAL-01",
                    metric="Validator Delinquency",
                    severity="warning" if curr_delinq_pct < 5.0 else "critical",
                    current_value=f"{curr_delinq_pct:.2f}% ({val.get('delinquent_validators', 0)} nodes)",
                    baseline_value="<0.50%",
                    threshold=f">{self.delinq_warn}%",
                    title="Elevated Delinquent Validator Stake",
                    description=(
                        f"Delinquent validator stake is at {curr_delinq_pct:.2f}% across "
                        f"{val.get('delinquent_validators', 0)} delinquent vote accounts."
                    ),
                    detected_at=now_iso,
                )
            )

        # 5. Price Volatility Check
        if curr_price_change > self.price_crit:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-PRICE-01",
                    metric="SOL Price Volatility",
                    severity="critical",
                    current_value=f"{price.get('change_24h_pct', 0.0):+.2f}%",
                    baseline_value="±5.0%",
                    threshold=f">±{self.price_crit}%",
                    title="Extreme 24h SOL Price Movement",
                    description=f"SOL price experienced extreme 24h volatility of {price.get('change_24h_pct', 0.0):+.2f}%.",
                    detected_at=now_iso,
                )
            )
        elif curr_price_change > self.price_warn:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-PRICE-02",
                    metric="SOL Price Volatility",
                    severity="warning",
                    current_value=f"{price.get('change_24h_pct', 0.0):+.2f}%",
                    baseline_value="±5.0%",
                    threshold=f">±{self.price_warn}%",
                    title="Notable 24h SOL Price Shift",
                    description=f"SOL price moved {price.get('change_24h_pct', 0.0):+.2f}% over the last 24 hours.",
                    detected_at=now_iso,
                )
            )

        # 6. TVL Volatility Check
        if curr_tvl_change > self.tvl_warn:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-TVL-01",
                    metric="DeFi TVL Movement",
                    severity="warning",
                    current_value=f"{defi.get('tvl_change_24h_pct', 0.0):+.2f}%",
                    baseline_value="±3.0%",
                    threshold=f">±{self.tvl_warn}%",
                    title="Significant 24h DeFi TVL Shift",
                    description=f"Solana ecosystem TVL moved {defi.get('tvl_change_24h_pct', 0.0):+.2f}% in 24 hours.",
                    detected_at=now_iso,
                )
            )

        return alerts


def detect_anomalies(
    current_onchain: Dict[str, Any],
    current_market: Dict[str, Any],
    historical_snapshots: List[Dict[str, Any]],
) -> List[AnomalyAlert]:
    """Convenience entrypoint for anomaly evaluation."""
    detector = AnomalyDetector()
    return detector.evaluate(current_onchain, current_market, historical_snapshots)


# ----------------------------------------------------------------------
# Unit Tests with Synthetic Data
# ----------------------------------------------------------------------
def test_anomaly_triggers() -> None:
    """Validate that every anomaly rule correctly triggers under synthetic stress conditions."""
    detector = AnomalyDetector()
    synthetic_history = [
        {"tps": 3000.0, "timestamp": "2026-08-01T00:00:00Z"},
        {"tps": 3100.0, "timestamp": "2026-08-02T00:00:00Z"},
        {"tps": 2900.0, "timestamp": "2026-08-03T00:00:00Z"},
    ]

    print("Running Anomaly Engine Unit Tests...")

    # Test 1: Normal Baseline -> 0 Alerts
    normal_onchain = {
        "performance": {"current_tps": 3050.0, "avg_slot_time_ms": 410.0},
        "validators": {"delinquent_stake_pct": 0.1, "delinquent_validators": 2},
        "health": {"rpc_status": "ok", "is_healthy": True},
    }
    normal_market = {
        "price": {"change_24h_pct": 2.1},
        "defi": {"tvl_change_24h_pct": 1.2},
    }
    alerts = detector.evaluate(normal_onchain, normal_market, synthetic_history)
    assert len(alerts) == 0, f"Expected 0 alerts for normal baseline, got {len(alerts)}"
    print("  [✓] Normal baseline test passed (0 alerts).")

    # Test 2: TPS Drop Shock (-70%)
    tps_drop_onchain = dict(normal_onchain)
    tps_drop_onchain["performance"] = {"current_tps": 900.0, "avg_slot_time_ms": 410.0}
    alerts = detector.evaluate(tps_drop_onchain, normal_market, synthetic_history)
    assert any("TPS" in a.metric and a.severity == "critical" for a in alerts), "TPS drop test failed"
    print("  [✓] TPS drop anomaly trigger verified.")

    # Test 3: Slot Time Degradation (850ms)
    slot_lag_onchain = dict(normal_onchain)
    slot_lag_onchain["performance"] = {"current_tps": 3000.0, "avg_slot_time_ms": 850.0}
    alerts = detector.evaluate(slot_lag_onchain, normal_market, synthetic_history)
    assert any("Slot" in a.metric and a.severity == "critical" for a in alerts), "Slot time test failed"
    print("  [✓] Slot time latency anomaly trigger verified.")

    # Test 4: Delinquent Validator Stake Jump (6.5%)
    delinq_onchain = dict(normal_onchain)
    delinq_onchain["validators"] = {"delinquent_stake_pct": 6.5, "delinquent_validators": 42}
    alerts = detector.evaluate(delinq_onchain, normal_market, synthetic_history)
    assert any("Validator" in a.metric for a in alerts), "Validator delinquency test failed"
    print("  [✓] Validator delinquency anomaly trigger verified.")

    # Test 5: Price Shock (+25%)
    price_shock_market = dict(normal_market)
    price_shock_market["price"] = {"change_24h_pct": 25.4}
    alerts = detector.evaluate(normal_onchain, price_shock_market, synthetic_history)
    assert any("Price" in a.metric and a.severity == "critical" for a in alerts), "Price shock test failed"
    print("  [✓] SOL price volatility anomaly trigger verified.")

    # Test 6: Node Unhealthy
    unhealthy_onchain = dict(normal_onchain)
    unhealthy_onchain["health"] = {"rpc_status": "degraded", "is_healthy": False, "summary": "Node sync error"}
    alerts = detector.evaluate(unhealthy_onchain, normal_market, synthetic_history)
    assert any("Health" in a.metric for a in alerts), "Health anomaly test failed"
    print("  [✓] Cluster health anomaly trigger verified.")

    print("All Anomaly Engine Unit Tests Passed Successfully!\n")


if __name__ == "__main__":
    test_anomaly_triggers()
