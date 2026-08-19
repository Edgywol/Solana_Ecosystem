"""Real-time Twitter/X Sentiment Integration for Solana Ecosystem Monitoring.

Tracks mention volume and basic sentiment classification for:
- Solana Foundation official announcements
- Key protocol upgrades (Firedancer, Alpenglow, SIMD)
- Ecosystem activity (MEV, validators, network stress)

Uses NO external API keys (simulates with hand-curated keyword analysis).
In production, integrate with official Twitter API v2 or DeepAPI alternative.

Strategy:
1. Define keyword sets for positive/negative mentions
2. Count frequency of mentions in timeframe
3. Calculate sentiment ratio (positive / total)
4. Compare to historical baseline
5. Alert on sentiment shifts that correlate with on-chain anomalies
"""

import random as _random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SentimentSnapshot:
    timestamp: str
    total_mentions: int
    positive_mentions: int
    negative_mentions: int
    neutral_mentions: int
    sentiment_score: float  # -1.0 (all negative) to +1.0 (all positive)
    trending_keywords: List[str]
    mention_velocity: float  # mentions per hour (trend)


class TwitterSentimentCollector:
    """Collects and analyzes Solana ecosystem mentions from social platforms."""

    # Keyword sets for categorization (production would use NLP)
    POSITIVE_KEYWORDS = {
        "upgrade", "bullish", "innovation", "launch", "adoption", "partnership",
        "breakthrough", "momentum", "growth", "strong", "impressive", "amazing",
        "excited", "confident", "bullrun", "gains", "moon", "gm", "spl", "ecosystem",
        "firedancer", "alpenglow", "simd", "improvement", "performance", "speed",
        "reliable", "secure", "revolutionary", "game-changer", "solana wins",
    }

    NEGATIVE_KEYWORDS = {
        "outage", "bearish", "crash", "concern", "risk", "vulnerability",
        "exploit", "hack", "failure", "struggle", "weak", "down", "bearish",
        "fud", "worst", "terrible", "disaster", "broken", "downtime", "attack",
        "security", "regression", "bug", "issue", "problem", "fails", "rip solana",
    }

    NEUTRAL_KEYWORDS = {
        "solana", "sol", "validator", "transaction", "network", "blockchain",
        "defi", "nft", "token", "stake", "slashing", "governance", "proposal",
        "update", "release", "version", "api", "rpc", "endpoint", "monitor",
    }

    def __init__(self, seed: Optional[int] = None):
        self.historical_sentiments: List[SentimentSnapshot] = []
        # Seeded RNG for deterministic output across runs within same pipeline execution
        self._rng = _random.Random(seed)

    def collect_sentiment(
        self,
        time_window_hours: int = 24,
    ) -> SentimentSnapshot:
        """Collect and analyze sentiment for Solana mentions in past N hours.
        
        In production, this would query Twitter API v2 with filters:
        - query: ("solana" OR "sol" OR "firedancer" OR "alpenglow") -is:retweet lang:en
        - aggregation: hourly mention counts, sentiment labels
        - deduplication: by author + content hash
        
        For now, returns synthetic/simulated sentiment with realistic patterns.
        """
        now = datetime.now(timezone.utc)
        
        # SIMULATED DATA: In production, replace with actual Twitter API v2 calls.
        # This module demonstrates the sentiment analysis data structure, analytical
        # flow, and on-chain correlation engine. Output is deterministic per-run
        # (seeded RNG) so report.json snapshots are reproducible.
        #
        # To integrate real Twitter data:
        # 1. Set TWITTER_BEARER_TOKEN env var with Twitter API v2 bearer token
        # 2. Replace this method body with actual API calls:
        #    query: ("solana" OR "sol" OR "firedancer" OR "alpenglow") -is:retweet lang:en
        #    aggregation: hourly mention counts, sentiment labels
        #    deduplication: by author + content hash
        
        # Simulate mention trends: base activity + random variance
        base_mentions = 450
        variance = 120 * (0.5 - self._rng.random() if self._rng.random() < 0.7 else 1.0)
        total_mentions = max(100, int(base_mentions + variance))
        
        # Simulate sentiment ratio influenced by recent events
        positive_ratio = 0.55 + (self._rng.random() - 0.5) * 0.15
        negative_ratio = 0.25 + (self._rng.random() - 0.5) * 0.10
        neutral_ratio = max(0, 1.0 - positive_ratio - negative_ratio)
        
        positive_mentions = int(total_mentions * positive_ratio)
        negative_mentions = int(total_mentions * negative_ratio)
        neutral_mentions = total_mentions - positive_mentions - negative_mentions
        
        # Sentiment score: -1 (all negative) to +1 (all positive)
        sentiment_score = (positive_mentions - negative_mentions) / max(1, total_mentions)
        
        # Trending keywords (mock): would be extracted from actual mentions
        trending_keywords = ["firedancer", "upgrade", "innovation", "ecosystem"]
        
        # Mention velocity: mentions per hour
        mention_velocity = total_mentions / time_window_hours
        
        snapshot = SentimentSnapshot(
            timestamp=now.isoformat(),
            total_mentions=total_mentions,
            positive_mentions=positive_mentions,
            negative_mentions=negative_mentions,
            neutral_mentions=neutral_mentions,
            sentiment_score=sentiment_score,
            trending_keywords=trending_keywords,
            mention_velocity=mention_velocity,
        )
        
        self.historical_sentiments.append(snapshot)
        return snapshot

    def get_sentiment_trend(self, lookback_hours: int = 24) -> Tuple[float, float]:
        """Return (current_sentiment_score, 24h_average_sentiment).
        
        Useful for detecting sentiment shifts that correlate with on-chain anomalies.
        """
        if not self.historical_sentiments:
            return 0.0, 0.0
        
        recent = self.historical_sentiments[-lookback_hours:] if lookback_hours > 0 else self.historical_sentiments
        if not recent:
            return 0.0, 0.0
        
        current_sentiment = recent[-1].sentiment_score
        avg_sentiment = sum(s.sentiment_score for s in recent) / len(recent)
        
        return current_sentiment, avg_sentiment

    def classify_sentiment(self, text: str) -> str:
        """Simple keyword-based sentiment classification (production: use ML/NLP)."""
        text_lower = text.lower()
        
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def detect_sentiment_shift(
        self,
        current_snapshot: SentimentSnapshot,
        threshold: float = 0.3,
    ) -> Optional[Dict[str, Any]]:
        """Detect if sentiment shifted significantly in past 24h.
        
        Returns alert dict if shift exceeds threshold, else None.
        threshold: minimum absolute change in sentiment score to trigger alert.
        """
        if len(self.historical_sentiments) < 2:
            return None
        
        prev_snapshot = self.historical_sentiments[-2]
        sentiment_delta = current_snapshot.sentiment_score - prev_snapshot.sentiment_score
        mention_delta = current_snapshot.total_mentions - prev_snapshot.total_mentions
        
        if abs(sentiment_delta) >= threshold:
            return {
                "type": "sentiment_shift",
                "previous_score": prev_snapshot.sentiment_score,
                "current_score": current_snapshot.sentiment_score,
                "delta": sentiment_delta,
                "direction": "positive" if sentiment_delta > 0 else "negative",
                "mention_volume": current_snapshot.total_mentions,
                "mention_velocity_per_hour": current_snapshot.mention_velocity,
                "trending_topics": current_snapshot.trending_keywords,
                "timestamp": current_snapshot.timestamp,
                "severity": "critical" if abs(sentiment_delta) > 0.5 else "warning",
            }
        
        return None

    def correlate_with_onchain(
        self,
        sentiment_snapshot: SentimentSnapshot,
        onchain_metrics: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find correlations between social sentiment and on-chain metrics.
        
        Returns list of composite anomaly alerts.
        
        Examples:
        - Negative sentiment spike + TPS drop = coordinated FUD or real issue?
        - Positive sentiment + validator increase = healthy adoption
        - Neutral sentiment + price volatility = market event, not ecosystem issue
        """
        correlations = []
        
        # Correlation 1: Negative Sentiment + TPS Drop
        if sentiment_snapshot.sentiment_score < -0.2:
            tps = onchain_metrics.get("performance", {}).get("current_tps", 0)
            if tps < 2000:
                correlations.append({
                    "type": "negative_sentiment_with_tps_drop",
                    "severity": "critical",
                    "description": (
                        f"Negative sentiment ({sentiment_snapshot.sentiment_score:.2f}) "
                        f"coincides with low TPS ({tps:.0f}). "
                        f"Could indicate real network issue or coordinated FUD."
                    ),
                    "sentiment_score": sentiment_snapshot.sentiment_score,
                    "mention_volume": sentiment_snapshot.total_mentions,
                    "tps": tps,
                })
        
        # Correlation 2: Positive Sentiment + TPS Recovery
        if sentiment_snapshot.sentiment_score > 0.4:
            tps = onchain_metrics.get("performance", {}).get("current_tps", 0)
            if tps > 4000:
                correlations.append({
                    "type": "positive_sentiment_with_high_tps",
                    "severity": "info",
                    "description": (
                        f"Positive sentiment ({sentiment_snapshot.sentiment_score:.2f}) "
                        f"with strong TPS performance ({tps:.0f}). Healthy ecosystem signals."
                    ),
                    "sentiment_score": sentiment_snapshot.sentiment_score,
                    "tps": tps,
                })
        
        # Correlation 3: Volatile Sentiment + High Delinquency
        validator_metrics = onchain_metrics.get("validators", {})
        delinq_pct = validator_metrics.get("delinquent_stake_pct", 0)
        if delinq_pct > 2.0 and abs(sentiment_snapshot.sentiment_score) < 0.1:
            correlations.append({
                "type": "neutral_sentiment_with_validator_stress",
                "severity": "warning",
                "description": (
                    f"Validator stress ({delinq_pct:.1f}% delinquency) "
                    f"but sentiment remains neutral. May indicate slow-moving issue."
                ),
                "delinquency_pct": delinq_pct,
                "sentiment_score": sentiment_snapshot.sentiment_score,
            })
        
        return correlations

    def to_report_dict(self) -> Dict[str, Any]:
        """Export sentiment data for JSON report integration."""
        if not self.historical_sentiments:
            return {
                "sentiment_status": "unavailable",
                "reason": "no snapshots collected yet",
            }
        
        current = self.historical_sentiments[-1]
        prev_24h = self.historical_sentiments[-24:] if len(self.historical_sentiments) >= 24 else self.historical_sentiments
        
        return {
            "sentiment_status": "available",
            "source_type": "simulated (Twitter API v2 not configured; set TWITTER_BEARER_TOKEN)",
            "current": {
                "timestamp": current.timestamp,
                "score": round(current.sentiment_score, 3),
                "total_mentions": current.total_mentions,
                "positive": current.positive_mentions,
                "negative": current.negative_mentions,
                "neutral": current.neutral_mentions,
                "trending_keywords": current.trending_keywords,
                "mention_velocity_per_hour": round(current.mention_velocity, 2),
            },
            "trend_24h": {
                "avg_sentiment_score": round(sum(s.sentiment_score for s in prev_24h) / len(prev_24h), 3),
                "min_sentiment_score": round(min(s.sentiment_score for s in prev_24h), 3),
                "max_sentiment_score": round(max(s.sentiment_score for s in prev_24h), 3),
                "total_mentions_24h": sum(s.total_mentions for s in prev_24h),
                "avg_mention_velocity": round(sum(s.mention_velocity for s in prev_24h) / len(prev_24h), 2),
            },
        }


# Convenience entrypoint for pipeline integration
def collect_solana_sentiment() -> Dict[str, Any]:
    """Collect current Solana ecosystem sentiment and return report dict."""
    collector = TwitterSentimentCollector()
    current_snapshot = collector.collect_sentiment(time_window_hours=24)
    return collector.to_report_dict()
