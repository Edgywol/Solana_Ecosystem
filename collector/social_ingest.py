"""Keyless social ingest: Twitter/X via Nitter RSS + Solana RSS fallback (stdlib only).

Tries multiple keyless RSS endpoints in order; first success wins. If all fail
(e.g., Nitter 403), falls back to Solana Foundation blog RSS and reports the
mode honestly. No API key, no fabrication — unavailable is reported as such."""

from __future__ import annotations

import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List

CANDIDATES = [
    # Nitter instances (keyless, may 403)
    ("nitter.net", "https://nitter.net/solana/rss"),
    ("nitter.privacydev.net", "https://nitter.privacydev.net/solana/rss"),
    # Solana Foundation blog RSS (reliable, keyless)
    ("solana.com", "https://solana.com/rss.xml"),
    # GitHub Solana SIMD feed as last resort
    ("github", "https://github.com/solana-foundation/solana-improvement-documents/commits/main.atom"),
]

POS_WORDS = {"launch","upgrade","release","growth","bullish","record","milestone","expansion","partnership","funding","approval"}
NEG_WORDS = {"outage","exploit","hack","down","delay","critical","halt","degraded","incident","breach"}


def _fetch_rss(url: str, timeout: int = 8) -> List[Dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "SolanaEcosystemDashboard/1.0", "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    # Try parse as RSS/Atom
    try:
        root = ET.fromstring(data)
    except Exception:
        return []
    items: List[Dict[str, str]] = []
    # RSS <item>
    for it in root.findall(".//item"):
        title = (it.findtext("title") or "").strip()
        pub = (it.findtext("pubDate") or it.findtext("published") or "").strip()
        link = (it.findtext("link") or "").strip()
        if title:
            items.append({"title": title, "date": pub, "link": link})
        if len(items) >= 20:
            break
    # Atom <entry>
    if not items:
        for it in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            t = it.find("{http://www.w3.org/2005/Atom}title")
            title = (t.text if t is not None else "").strip()
            link_el = it.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href") if link_el is not None else ""
            if title:
                items.append({"title": title, "date": "", "link": link})
            if len(items) >= 20:
                break
    return items


def _sentiment_of(text: str) -> str:
    low = text.lower()
    pos = sum(1 for w in POS_WORDS if w in low)
    neg = sum(1 for w in NEG_WORDS if w in low)
    if pos > neg:
        return "bullish"
    if neg > pos:
        return "bearish"
    return "neutral"


def collect_social_feed() -> Dict[str, Any]:
    """Attempt keyless social ingest; returns status + items."""
    for name, url in CANDIDATES:
        try:
            items = _fetch_rss(url)
            if items:
                for it in items:
                    it["sentiment"] = _sentiment_of(it["title"])
                bullish = sum(1 for i in items if i["sentiment"] == "bullish")
                bearish = sum(1 for i in items if i["sentiment"] == "bearish")
                return {
                    "ingest_status": "live",
                    "source_type": f"RSS ({name}, no API key)",
                    "source_url": url,
                    "items": items[:12],
                    "summary": {"total": len(items), "bullish": bullish, "bearish": bearish, "neutral": len(items)-bullish-bearish},
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            print(f"[social] {name} fetch failed: {e}")
            continue
    return {
        "ingest_status": "unavailable",
        "source_type": "RSS (all keyless endpoints unavailable this run)",
        "reason": "Nitter instances returned 403 and fallback RSS unavailable — reported as unavailable rather than fabricated",
        "items": [],
    }
