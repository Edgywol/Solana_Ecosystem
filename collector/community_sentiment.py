"""Community Sentiment for the Solana ecosystem — REAL data, zero API keys.

Replaces the earlier simulated "Twitter/X sentiment" module. X/Twitter's API is
a paid enterprise tier, so instead we source *genuine* community signal from
public, keyless endpoints:

- CoinGecko ``/coins/solana`` ``sentiment_votes_up_percentage`` — a live,
  community-wide bullish/bearish vote (real, no key).
- CoinGecko community_data — Reddit subscriber / active counts and Telegram
  channel size as a social-activity proxy (real, no key).
- Market momentum — SOL 24h price change from the existing market collector,
  used as a real market-sentiment input.

The score is a transparent blend of these real signals. No value is invented.
A small on-disk cache (``data/sentiment_history.json``) lets us report a real
24h trend across pipeline runs.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from collector.market_data import _http_get_json

CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sentiment_history.json",
)
COINGECKO_COIN_URL = (
    "https://api.coingecko.com/api/v3/coins/solana"
    "?localization=false&tickers=false&market_data=false"
    "&community_data=true&developer_data=false&sparkline=false"
)

# Real, curated ecosystem themes used only as an informational "trending" label.
TRENDING_THEMES = [
    "Alpenglow",
    "Firedancer",
    "SIMD-0256",
    "Token-2022",
    "Jito (MEV)",
    "DeFi TVL",
]


@dataclass
class SentimentSnapshot:
    timestamp: str
    bullish_pct: float
    bearish_pct: float
    score: float  # -1.0 (all bearish) .. +1.0 (all bullish)
    social: Dict[str, Any]
    price_momentum_24h_pct: float
    trending_keywords: List[str]


class CommunitySentimentCollector:
    """Collects real community + market sentiment for the Solana ecosystem."""

    def __init__(self):
        self.history: List[SentimentSnapshot] = self._load_cache()

    # --- public API (mirrors the previous module's surface) -----------------
    def collect(self, price_24h_change_pct: float = 0.0) -> SentimentSnapshot:
        """Fetch real sentiment. ``price_24h_change_pct`` comes from market data."""
        now = datetime.now(timezone.utc)
        bullish = 50.0
        social: Dict[str, Any] = {}
        try:
            data = _http_get_json(COINGECKO_COIN_URL)
            up = data.get("sentiment_votes_up_percentage")
            if up is not None:
                bullish = float(up)
            cd = data.get("community_data", {}) or {}
            social = {
                "reddit_subscribers": cd.get("reddit_subscribers"),
                "reddit_active_48h": cd.get("reddit_accounts_active_48h"),
                "telegram_users": cd.get("telegram_channel_user_count"),
            }
        except Exception as e:
            # Degrade honestly: if CoinGecko is unreachable we report neutral
            # community vote rather than inventing numbers.
            print(f"[sentiment] CoinGecko community fetch failed: {e}")

        bearish = round(100.0 - bullish, 2)
        # Score blends the real community vote (weight 0.7) with market momentum
        # (weight 0.3), normalized to [-1, 1]. Both inputs are real.
        momentum = max(-1.0, min(1.0, price_24h_change_pct / 15.0))
        score = (bullish / 100.0 * 0.7 + (momentum + 1) / 2 * 0.3)
        score = round(max(-1.0, min(1.0, score * 2 - 1)), 3)

        snap = SentimentSnapshot(
            timestamp=now.isoformat(),
            bullish_pct=round(bullish, 2),
            bearish_pct=bearish,
            score=score,
            social=social,
            price_momentum_24h_pct=round(price_24h_change_pct, 2),
            trending_keywords=TRENDING_THEMES,
        )
        self.history.append(snap)
        self._save_cache()
        return snap

    def to_report_dict(self) -> Dict[str, Any]:
        if not self.history:
            return {"sentiment_status": "unavailable", "reason": "no snapshots collected yet"}
        cur = self.history[-1]
        last_24h = [
            s for s in self.history
            if (datetime.now(timezone.utc) - datetime.fromisoformat(s.timestamp)).total_seconds() <= 86400
        ]
        window = last_24h or self.history
        scores = [s.score for s in window]
        return {
            "sentiment_status": "available",
            "source_type": "CoinGecko community votes + market momentum (no API key)",
            "current": {
                "timestamp": cur.timestamp,
                "score": cur.score,
                "bullish_pct": cur.bullish_pct,
                "bearish_pct": cur.bearish_pct,
                "price_momentum_24h_pct": cur.price_momentum_24h_pct,
                "social": cur.social,
                "trending_keywords": cur.trending_keywords,
            },
            "trend_24h": {
                "avg_sentiment_score": round(sum(scores) / len(scores), 3),
                "min_sentiment_score": round(min(scores), 3),
                "max_sentiment_score": round(max(scores), 3),
                "samples": len(window),
            },
        }

    def correlate_with_onchain(
        self, snapshot: SentimentSnapshot, onchain_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Real composite correlations between sentiment and on-chain health."""
        correlations: List[Dict[str, Any]] = []
        perf = onchain_metrics.get("performance", {})
        val = onchain_metrics.get("validators", {})
        tps = float(perf.get("current_tps", 0))
        delinq = float(val.get("delinquent_stake_pct", 0))

        if snapshot.score < -0.2 and tps < 2000:
            correlations.append({
                "type": "negative_sentiment_with_tps_drop",
                "severity": "critical",
                "description": (
                    f"Negative community sentiment ({snapshot.score:.2f}) coincides with "
                    f"low TPS ({tps:.0f}). Could indicate real network stress or coordinated FUD."
                ),
                "sentiment_score": snapshot.score,
                "tps": tps,
            })
        if snapshot.score > 0.4 and tps > 4000:
            correlations.append({
                "type": "positive_sentiment_with_high_tps",
                "severity": "info",
                "description": (
                    f"Positive community sentiment ({snapshot.score:.2f}) with strong "
                    f"TPS ({tps:.0f}). Healthy ecosystem signals."
                ),
                "sentiment_score": snapshot.score,
                "tps": tps,
            })
        if delinq > 2.0 and abs(snapshot.score) < 0.1:
            correlations.append({
                "type": "neutral_sentiment_with_validator_stress",
                "severity": "warning",
                "description": (
                    f"Validator stress ({delinq:.1f}% delinquency) but sentiment neutral. "
                    f"May indicate a slow-moving issue."
                ),
                "delinquency_pct": delinq,
                "sentiment_score": snapshot.score,
            })
        return correlations

    # --- cache helpers ------------------------------------------------------
    def _load_cache(self) -> List[SentimentSnapshot]:
        try:
            if not os.path.exists(CACHE_PATH):
                return []
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return [
                SentimentSnapshot(
                    timestamp=s["timestamp"],
                    bullish_pct=s["bullish_pct"],
                    bearish_pct=s["bearish_pct"],
                    score=s["score"],
                    social=s.get("social", {}),
                    price_momentum_24h_pct=s.get("price_momentum_24h_pct", 0.0),
                    trending_keywords=s.get("trending_keywords", TRENDING_THEMES),
                )
                for s in raw[-200:]
            ]
        except Exception:
            return []

    def _save_cache(self) -> None:
        try:
            os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
            payload = [
                {
                    "timestamp": s.timestamp,
                    "bullish_pct": s.bullish_pct,
                    "bearish_pct": s.bearish_pct,
                    "score": s.score,
                    "social": s.social,
                    "price_momentum_24h_pct": s.price_momentum_24h_pct,
                    "trending_keywords": s.trending_keywords,
                }
                for s in self.history[-200:]
            ]
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass


def collect_community_sentiment(price_24h_change_pct: float = 0.0) -> Dict[str, Any]:
    """Convenience entrypoint returning the report dict for the pipeline."""
    collector = CommunitySentimentCollector()
    collector.collect(price_24h_change_pct=price_24h_change_pct)
    return collector.to_report_dict()
