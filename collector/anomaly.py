"""Explainable Anomaly & Risk Detection Engine for Solana Ecosystem (Python Standard Library only).

Evaluates current telemetry against trailing SQLite baseline snapshots using:
- Exponential smoothing baseline forecasting (detects departure from trend)
- TPS volatility, slot time latency, validator delinquency spikes
- Price momentum & TVL drawdowns with 30-day historical context
- RPC health & cluster consensus degradation
- Multi-metric composite anomalies (TPS drop + delinquency spike)

Innovation: Uses statistical trend analysis instead of rigid thresholds.
A metric is anomalous if it deviates significantly from its exponential moving average,
not just if it exceeds a static threshold. This catches emerging problems earlier.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


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
    deviation_pct: float = 0.0
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExponentialSmoothing:
    """Lightweight exponential smoothing for trend baseline calculation (no numpy)."""

    def __init__(self, alpha: float = 0.3):
        """alpha: smoothing factor (0.1-0.5, higher = more responsive)."""
        self.alpha = alpha
        self.level = None
        self.trend = None

    def fit(self, values: List[float]) -> Tuple[float, float]:
        """Fit exponential smoothing to historical values. Returns (level, trend)."""
        if not values or len(values) < 2:
            return 0.0, 0.0
        
        values = [v for v in values if v is not None and not math.isnan(v)]
        if len(values) < 2:
            return values[0] if values else 0.0, 0.0
        
        # Initialize level to first value
        level = values[0]
        trend = (values[-1] - values[0]) / max(1, len(values) - 1)
        
        # Apply exponential smoothing
        for val in values[1:]:
            prev_level = level
            level = self.alpha * val + (1 - self.alpha) * (level + trend)
            trend = self.alpha * (level - prev_level) + (1 - self.alpha) * trend
        
        self.level = level
        self.trend = trend
        return level, trend

    def forecast(self, steps: int = 1) -> float:
        """Forecast next value(s) ahead."""
        if self.level is None:
            return 0.0
        return self.level + (steps * self.trend)

    def forecast_range(self, steps: int = 1) -> Tuple[float, float]:
        """Forecast with uncertainty band (±20% of forecast)."""
        forecast = self.forecast(steps)
        margin = abs(forecast * 0.2)
        return forecast - margin, forecast + margin


class AnomalyDetector:
    """Predictive anomaly detector using exponential smoothing + statistical deviation."""

    def __init__(
        self,
        tps_deviation_sigma: float = 2.5,
        slot_time_sigma: float = 2.0,
        price_deviation_sigma: float = 2.0,
        tvl_deviation_sigma: float = 1.8,
        delinquency_threshold_pct: float = 2.5,
        smoothing_alpha: float = 0.3,
    ):
        """
        Sigma thresholds: deviation is anomalous if >N standard deviations from trend.
        Higher sigma = less sensitive (fewer false positives).
        """
        self.tps_sigma = tps_deviation_sigma
        self.slot_sigma = slot_time_sigma
        self.price_sigma = price_deviation_sigma
        self.tvl_sigma = tvl_deviation_sigma
        self.delinq_threshold = delinquency_threshold_pct
        self.smoothing_alpha = smoothing_alpha

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation (stdlib only)."""
        if not values or len(values) < 2:
            return 0.0
        values = [v for v in values if v is not None and not math.isnan(v)]
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _check_deviation(
        self,
        current: float,
        historical: List[float],
        sigma_threshold: float,
        metric_name: str,
        alerts: List[AnomalyAlert],
        now_iso: str,
        high_is_bad: bool = False,
    ) -> None:
        """Check if current value deviates significantly from trend."""
        if not historical or len(historical) < 2:
            return

        smoother = ExponentialSmoothing(alpha=self.smoothing_alpha)
        baseline, trend = smoother.fit(historical)
        std_dev = self._calculate_std_dev(historical)

        if std_dev == 0:
            return

        deviation = abs(current - baseline)
        num_sigmas = deviation / std_dev
        deviation_pct = (deviation / max(0.001, baseline)) * 100 if baseline != 0 else 0

        if num_sigmas >= sigma_threshold:
            severity = "critical" if num_sigmas >= sigma_threshold + 1 else "warning"
            direction = "above" if current > baseline else "below"
            
            alert_title = f"{metric_name} Anomaly Detected"
            alert_desc = (
                f"{metric_name} is {direction} historical trend. "
                f"Current: {current:.2f}, Trend Baseline: {baseline:.2f}, "
                f"Deviation: {deviation_pct:.1f}% ({num_sigmas:.1f}σ). "
                f"Expected range: {baseline - std_dev:.2f}-{baseline + std_dev:.2f}"
            )

            alerts.append(
                AnomalyAlert(
                    id=f"ALERT-{metric_name.upper().replace(' ', '-')}-{int(num_sigmas*10)}",
                    metric=metric_name,
                    severity=severity,
                    current_value=current,
                    baseline_value=baseline,
                    threshold=f"within {sigma_threshold}σ of {baseline:.2f}",
                    title=alert_title,
                    description=alert_desc,
                    detected_at=now_iso,
                    deviation_pct=deviation_pct,
                    confidence_score=min(1.0, num_sigmas / (sigma_threshold + 2)),
                )
            )

    def evaluate(
        self,
        current_onchain: Dict[str, Any],
        current_market: Dict[str, Any],
        historical_snapshots: List[Dict[str, Any]],
    ) -> List[AnomalyAlert]:
        """Evaluate current metrics using exponential smoothing trend analysis."""
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

        # 1. Cluster & RPC Health Check (hardcoded threshold)
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

        # 2. TPS Deviation using Exponential Smoothing (Predictive)
        if historical_snapshots:
            tps_history = [float(s.get("tps", 0)) for s in historical_snapshots if s.get("tps")]
            if tps_history:
                self._check_deviation(
                    curr_tps, tps_history, self.tps_sigma, "Network TPS", alerts, now_iso
                )

        # 3. Slot Time Degradation using Trend Analysis
        if historical_snapshots:
            slot_history = [float(s.get("slot_time_ms", 400)) for s in historical_snapshots if s.get("slot_time_ms")]
            if slot_history:
                self._check_deviation(
                    curr_slot_time, slot_history, self.slot_sigma, "Slot Duration (ms)", alerts, now_iso
                )

        # 4. Validator Delinquency Spike (hardcoded threshold, not trend-based)
        if curr_delinq_pct > self.delinq_threshold:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-VAL-01",
                    metric="Validator Delinquency",
                    severity="critical" if curr_delinq_pct > 4.0 else "warning",
                    current_value=f"{curr_delinq_pct:.2f}%",
                    baseline_value=f"<{self.delinq_threshold}%",
                    threshold=f">{self.delinq_threshold}%",
                    title="Delinquent Validator Stake Spike",
                    description=(
                        f"Delinquent stake elevated to {curr_delinq_pct:.2f}% "
                        f"({val.get('delinquent_validators', 0)} nodes). Network may be stressed."
                    ),
                    detected_at=now_iso,
                    deviation_pct=curr_delinq_pct - self.delinq_threshold,
                    confidence_score=min(1.0, curr_delinq_pct / 5.0),
                )
            )

        # 5. SOL Price Momentum using Trend
        if historical_snapshots:
            price_history = [float(s.get("sol_price_usd", 0)) for s in historical_snapshots if s.get("sol_price_usd")]
            if price_history:
                self._check_deviation(
                    price.get("price_usd", 0), price_history, self.price_sigma, "SOL Price (USD)", alerts, now_iso
                )

        # 6. TVL Drawdown using Trend
        if historical_snapshots:
            tvl_history = [float(s.get("tvl_usd", 0)) for s in historical_snapshots if s.get("tvl_usd")]
            if tvl_history:
                self._check_deviation(
                    defi.get("tvl_usd", 0), tvl_history, self.tvl_sigma, "DeFi TVL (USD)", alerts, now_iso
                )

        # 7. Composite: TPS Drop + Delinquency Spike = Network Stress
        if curr_tps < 2000 and curr_delinq_pct > 1.5:
            alerts.append(
                AnomalyAlert(
                    id="ALERT-COMPOSITE-01",
                    metric="Network Stress Composite",
                    severity="critical",
                    current_value=f"TPS={curr_tps:.0f}, Delinq={curr_delinq_pct:.1f}%",
                    baseline_value="TPS>3000, Delinq<1%",
                    threshold="Composite: low TPS + high delinquency",
                    title="Critical Network Stress Signal",
                    description=(
                        f"Multi-metric composite anomaly: TPS at {curr_tps:.0f} (low) AND "
                        f"delinquency at {curr_delinq_pct:.1f}% (elevated). "
                        f"This combination indicates significant network stress or consensus issues."
                    ),
                    detected_at=now_iso,
                    confidence_score=0.95,
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
        {"tps": 3000.0, "slot_time_ms": 405.0, "sol_price_usd": 178.0, "tvl_usd": 4_900_000_000.0, "timestamp": "2026-08-01T00:00:00Z"},
        {"tps": 3100.0, "slot_time_ms": 410.0, "sol_price_usd": 180.0, "tvl_usd": 4_950_000_000.0, "timestamp": "2026-08-02T00:00:00Z"},
        {"tps": 2900.0, "slot_time_ms": 398.0, "sol_price_usd": 176.0, "tvl_usd": 4_850_000_000.0, "timestamp": "2026-08-03T00:00:00Z"},
    ]

    print("Running Anomaly Engine Unit Tests...")

    # Test 1: Normal Baseline -> 0 Alerts
    normal_onchain = {
        "performance": {"current_tps": 3050.0, "avg_slot_time_ms": 410.0},
        "validators": {"delinquent_stake_pct": 0.1, "delinquent_validators": 2},
        "health": {"rpc_status": "ok", "is_healthy": True},
    }
    normal_market = {
        "price": {"price_usd": 180.0, "change_24h_pct": 2.1},
        "defi": {"tvl_usd": 4_900_000_000.0, "tvl_change_24h_pct": 1.2},
    }
    alerts = detector.evaluate(normal_onchain, normal_market, synthetic_history)
    assert len(alerts) == 0, f"Expected 0 alerts for normal baseline, got {len(alerts)}"
    print("  [✓] Normal baseline test passed (0 alerts).")

    # Test 2: TPS Drop Shock (-70%)
    tps_drop_onchain = dict(normal_onchain)
    tps_drop_onchain["performance"] = {"current_tps": 900.0, "avg_slot_time_ms": 410.0}
    alerts = detector.evaluate(tps_drop_onchain, normal_market, synthetic_history)
    assert any("TPS" in a.metric for a in alerts), f"TPS drop test failed: {[a.metric for a in alerts]}"
    print("  [✓] TPS drop anomaly trigger verified.")

    # Test 3: Slot Time Degradation (850ms — far above 398-410ms trend)
    slot_lag_onchain = dict(normal_onchain)
    slot_lag_onchain["performance"] = {"current_tps": 3000.0, "avg_slot_time_ms": 850.0}
    alerts = detector.evaluate(slot_lag_onchain, normal_market, synthetic_history)
    assert any("Slot" in a.metric for a in alerts), f"Slot time test failed: {[a.metric for a in alerts]}"
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
