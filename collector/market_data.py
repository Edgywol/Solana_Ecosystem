"""Solana Off-chain Market & Economic Data Collector (Python Standard Library only).

Aggregates public market data from DeFiLlama and CoinGecko with zero API keys:
- SOL spot price, 24h price delta, market capitalization, 24h trading volume
- Solana DeFi TVL, 30-day historical trend, 24h DEX volume, and stablecoin market cap
- Derived economic indicators: Real Economic Value (REV) proxy, median fee estimates, capital velocity
"""

from __future__ import annotations

import gzip
import json
import logging
import time
import urllib.error
import urllib.request
import zlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("market_data")

USER_AGENT = "SolanaEcosystemDashboard/1.0 (+https://github.com/chmgx81/solana-ecosystem-dashboard)"
REQUEST_TIMEOUT = 12


def _http_get_json(url: str, timeout: int = REQUEST_TIMEOUT) -> Any:
    """Perform HTTP GET request with gzip/deflate decoding and JSON parsing."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw_body = response.read()
        encoding = response.info().get("Content-Encoding", "").lower()
        if "gzip" in encoding or raw_body.startswith(b"\x1f\x8b"):
            raw_body = gzip.decompress(raw_body)
        elif "deflate" in encoding:
            raw_body = zlib.decompress(raw_body)
        return json.loads(raw_body.decode("utf-8"))


@dataclass
class SolPriceMetrics:
    price_usd: float = 0.0
    change_24h_pct: float = 0.0
    market_cap_usd: float = 0.0
    volume_24h_usd: float = 0.0
    last_updated_at: Optional[str] = None


@dataclass
class DeFiMetrics:
    tvl_usd: float = 0.0
    tvl_change_24h_pct: float = 0.0
    dex_volume_24h_usd: float = 0.0
    stablecoin_mcap_usd: float = 0.0
    capital_efficiency_ratio: float = 0.0
    historical_tvl_30d: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EconomicIndicators:
    base_fee_sol: float = 0.000005
    median_fee_sol: float = 0.000028
    median_fee_usd: float = 0.005
    rev_24h_usd: float = 0.0
    rev_methodology: str = (
        "Proxy calculated from estimated daily non-vote transactions * (base fee + median priority fee) "
        "+ estimated Jito MEV tips."
    )
    velocity_ratio: float = 0.0


@dataclass
class MarketData:
    collected_at: str
    status: str
    price: SolPriceMetrics
    defi: DeFiMetrics
    economics: EconomicIndicators
    sources: Dict[str, str] = field(
        default_factory=lambda: {
            "price_source": "CoinGecko / Binance Fallback",
            "defi_source": "DeFiLlama Public API",
            "stablecoins_source": "DeFiLlama Stablecoins API",
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketDataCollector:
    """Collects price, DeFi, and derived economic metrics without requiring API keys."""

    def fetch_sol_price(self) -> SolPriceMetrics:
        """Fetch SOL price, 24h change, and volume from CoinGecko with Binance fallback."""
        # Attempt 1: CoinGecko
        cg_url = (
            "https://api.coingecko.com/api/v3/simple/price?"
            "ids=solana&vs_currencies=usd&include_24hr_vol=true&"
            "include_24hr_change=true&include_market_cap=true"
        )
        try:
            data = _http_get_json(cg_url)
            sol_data = data.get("solana", {})
            if sol_data and "usd" in sol_data:
                return SolPriceMetrics(
                    price_usd=round(float(sol_data.get("usd", 0.0)), 2),
                    change_24h_pct=round(float(sol_data.get("usd_24h_change", 0.0)), 2),
                    market_cap_usd=round(float(sol_data.get("usd_market_cap", 0.0)), 2),
                    volume_24h_usd=round(float(sol_data.get("usd_24h_vol", 0.0)), 2),
                    last_updated_at=datetime.now(timezone.utc).isoformat(),
                )
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed: {e}. Trying Binance fallback...")

        # Fallback: Binance 24hr ticker
        binance_url = "https://api.binance.com/api/v3/ticker/24hr?symbol=SOLUSDT"
        try:
            b_data = _http_get_json(binance_url)
            price = float(b_data.get("lastPrice", 0.0))
            change_pct = float(b_data.get("priceChangePercent", 0.0))
            volume_quote = float(b_data.get("quoteVolume", 0.0))
            return SolPriceMetrics(
                price_usd=round(price, 2),
                change_24h_pct=round(change_pct, 2),
                market_cap_usd=0.0,  # Not returned by Binance ticker
                volume_24h_usd=round(volume_quote, 2),
                last_updated_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            logger.error(f"Binance fallback failed: {e}")

        return SolPriceMetrics()

    def fetch_defi_metrics(self) -> DeFiMetrics:
        """Fetch TVL, DEX volume, and stablecoin metrics from DeFiLlama."""
        tvl = 0.0
        tvl_change_24h = 0.0
        dex_vol = 0.0
        stables_mcap = 0.0
        hist_tvl_30d: List[Dict[str, Any]] = []

        # 1. Chains TVL
        try:
            chains = _http_get_json("https://api.llama.fi/v2/chains")
            sol_chain = next((c for c in chains if c.get("name") == "Solana"), None)
            if sol_chain:
                tvl = round(float(sol_chain.get("tvl", 0.0)), 2)
        except Exception as e:
            logger.warning(f"DeFiLlama TVL fetch failed: {e}")

        # 2. Historical Chain TVL (last 30 days)
        try:
            hist_tvl = _http_get_json("https://api.llama.fi/v2/historicalChainTvl/Solana")
            if isinstance(hist_tvl, list) and hist_tvl:
                # Take the last 30 daily points
                recent_30 = hist_tvl[-30:]
                hist_tvl_30d = [
                    {
                        "date": datetime.fromtimestamp(pt.get("date", 0), timezone.utc).strftime("%Y-%m-%d"),
                        "tvl": round(float(pt.get("tvl", 0.0)), 2),
                    }
                    for pt in recent_30
                ]
                if len(hist_tvl_30d) >= 2:
                    prev_tvl = hist_tvl_30d[-2]["tvl"]
                    curr_tvl = hist_tvl_30d[-1]["tvl"]
                    if prev_tvl > 0:
                        tvl_change_24h = round(((curr_tvl - prev_tvl) / prev_tvl) * 100, 2)
        except Exception as e:
            logger.warning(f"DeFiLlama historical TVL fetch failed: {e}")

        # 3. Solana DEX Volume
        try:
            dex_data = _http_get_json(
                "https://api.llama.fi/overview/dexs/solana?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"
            )
            dex_vol = round(float(dex_data.get("total24h", 0.0)), 2)
        except Exception as e:
            logger.warning(f"DeFiLlama DEX volume fetch failed: {e}")

        # 4. Stablecoins on Solana
        try:
            stable_chains = _http_get_json("https://stablecoins.llama.fi/stablecoinchains")
            sol_stables = next((c for c in stable_chains if c.get("name") == "Solana"), None)
            if sol_stables:
                stables_mcap = round(
                    float(sol_stables.get("totalCirculatingUSD", {}).get("peggedUSD", 0.0)), 2
                )
        except Exception as e:
            logger.warning(f"DeFiLlama stablecoin fetch failed: {e}")

        cap_eff = round(dex_vol / tvl, 3) if tvl > 0 else 0.0

        return DeFiMetrics(
            tvl_usd=tvl,
            tvl_change_24h_pct=tvl_change_24h,
            dex_volume_24h_usd=dex_vol,
            stablecoin_mcap_usd=stables_mcap,
            capital_efficiency_ratio=cap_eff,
            historical_tvl_30d=hist_tvl_30d,
        )

    def derive_economics(
        self, price: SolPriceMetrics, defi: DeFiMetrics, est_daily_tx: int = 45000000,
        measured_median_fee_sol: Optional[float] = None,
    ) -> EconomicIndicators:
        """Calculate derived economic velocity and Real Economic Value (REV) proxy.
        
        Methodology:
        - Base tx fee on Solana is a protocol constant of 5,000 lamports (0.000005 SOL).
        - Median priority fee is measured from live ``getRecentPrioritizationFees`` RPC
          samples when available (preferred); otherwise a conservative model default
          of ~0.000023 SOL is used as a fallback.
        - Estimated REV = (Estimated daily non-vote transactions * median fee in USD)
          + (Estimated daily Jito MEV tips).
        - Capital Velocity = 24h DEX Volume / TVL.
        """
        sol_price = price.price_usd if price.price_usd > 0 else 180.0
        base_fee_sol = 0.000005
        if measured_median_fee_sol and measured_median_fee_sol > 0:
            median_fee_sol = round(base_fee_sol + measured_median_fee_sol, 9)
        else:
            median_fee_sol = 0.000028
        median_fee_usd = round(median_fee_sol * sol_price, 4)

        # Estimate daily non-vote transactions (~25-35% of total tx)
        est_daily_non_vote = int(est_daily_tx * 0.30)
        daily_fee_revenue_usd = est_daily_non_vote * median_fee_usd
        # Daily Jito MEV tips estimate (~$400k - $1.2M depending on volume)
        est_daily_mev_usd = min(1500000.0, max(250000.0, defi.dex_volume_24h_usd * 0.0004))
        rev_24h_usd = round(daily_fee_revenue_usd + est_daily_mev_usd, 2)

        velocity = round(defi.dex_volume_24h_usd / max(1.0, defi.tvl_usd), 3)

        return EconomicIndicators(
            base_fee_sol=base_fee_sol,
            median_fee_sol=median_fee_sol,
            median_fee_usd=median_fee_usd,
            rev_24h_usd=rev_24h_usd,
            velocity_ratio=velocity,
        )

    def collect(self) -> MarketData:
        """Run full market data collection cycle."""
        now_iso = datetime.now(timezone.utc).isoformat()
        price = self.fetch_sol_price()
        defi = self.fetch_defi_metrics()
        economics = self.derive_economics(price, defi)

        status = "complete" if price.price_usd > 0 and defi.tvl_usd > 0 else "partial"

        return MarketData(
            collected_at=now_iso,
            status=status,
            price=price,
            defi=defi,
            economics=economics,
        )


def collect_market_data() -> MarketData:
    """Convenience helper to collect market data."""
    collector = MarketDataCollector()
    return collector.collect()


if __name__ == "__main__":
    print("Collecting off-chain market & economic metrics...")
    data = collect_market_data()
    print(json.dumps(data.to_dict(), indent=2))
