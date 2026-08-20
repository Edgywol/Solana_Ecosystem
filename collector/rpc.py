"""Solana JSON-RPC Client (Python Standard Library only).

Provides a resilient, zero-dependency interface to Solana mainnet-beta JSON-RPC.
Supports configurable endpoints via SOLANA_RPC_URL, gzip compression decoding,
and automatic failover across public RPC endpoints.
"""

from __future__ import annotations

import gzip
import http.client
import json
import logging
import os
import time
import urllib.error
import urllib.request
import zlib
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger("solana_rpc")

# Primary & Fallback RPC endpoints
DEFAULT_RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
FALLBACK_RPC_URLS = [
    "https://api.mainnet-beta.solana.com",
    "https://rpc.ankr.com/solana",
    "https://solana.drpc.org",
]

DEFAULT_TIMEOUT = 18  # seconds
USER_AGENT = "SolanaEcosystemDashboard/1.0 (+https://github.com/chmgx81/solana-ecosystem-dashboard)"


class SolanaRPCError(Exception):
    """Raised when an RPC request fails after all retries."""
    pass


class SolanaRPCClient:
    """Thin JSON-RPC client interacting directly with Solana RPC endpoints."""

    def __init__(self, endpoint: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self.primary_endpoint = endpoint or DEFAULT_RPC_URL
        self.endpoints = [self.primary_endpoint] + [
            url for url in FALLBACK_RPC_URLS if url != self.primary_endpoint
        ]
        self.timeout = timeout
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def call(self, method: str, params: Optional[Union[List[Any], Dict[str, Any]]] = None) -> Any:
        """Execute a JSON-RPC request with multi-endpoint fallback and retry logic."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params if params is not None else [],
        }
        encoded_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }

        last_err: Optional[Exception] = None

        for endpoint in self.endpoints:
            for attempt in range(1, 3):
                try:
                    req = urllib.request.Request(
                        endpoint,
                        data=encoded_data,
                        headers=headers,
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        raw_body = response.read()
                        encoding = response.info().get("Content-Encoding", "").lower()
                        if "gzip" in encoding or raw_body.startswith(b"\x1f\x8b"):
                            raw_body = gzip.decompress(raw_body)
                        elif "deflate" in encoding:
                            raw_body = zlib.decompress(raw_body)

                        body_str = raw_body.decode("utf-8")
                        resp_json = json.loads(body_str)

                        if "error" in resp_json:
                            err_msg = resp_json["error"].get("message", str(resp_json["error"]))
                            logger.warning(
                                f"RPC error from {endpoint} on method {method}: {err_msg}"
                            )
                            last_err = SolanaRPCError(f"RPC error: {err_msg}")
                            break  # Move to next endpoint

                        if "result" in resp_json:
                            return resp_json["result"]

                        return resp_json

                except http.client.IncompleteRead as e:
                    logger.warning(f"IncompleteRead on {endpoint} ({method}), attempting partial parse...")
                    try:
                        raw_body = e.partial
                        if raw_body.startswith(b"\x1f\x8b"):
                            raw_body = gzip.decompress(raw_body)
                        resp_json = json.loads(raw_body.decode("utf-8"))
                        if "result" in resp_json:
                            return resp_json["result"]
                    except Exception as parse_err:
                        last_err = parse_err
                        logger.warning(f"Failed to recover incomplete payload: {parse_err}")
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                    last_err = e
                    logger.warning(
                        f"Attempt {attempt} failed for {endpoint} ({method}): {e}"
                    )
                    time.sleep(0.4 * attempt)

        raise SolanaRPCError(
            f"All RPC endpoints failed for method '{method}'. Last error: {last_err}"
        )

    def get_health(self) -> str:
        """Get the current health of the node (returns 'ok' if healthy)."""
        try:
            res = self.call("getHealth")
            return "ok" if res == "ok" else str(res)
        except Exception as e:
            logger.warning(f"getHealth failed: {e}")
            return "degraded"

    def get_slot(self) -> Optional[int]:
        """Get current slot."""
        try:
            return int(self.call("getSlot", [{"commitment": "confirmed"}]))
        except Exception as e:
            logger.error(f"getSlot failed: {e}")
            return None

    def get_block_time(self, slot: int) -> Optional[int]:
        """Get Unix timestamp for a given slot."""
        try:
            res = self.call("getBlockTime", [slot])
            return int(res) if res is not None else None
        except Exception as e:
            logger.warning(f"getBlockTime for slot {slot} failed: {e}")
            return None

    def get_epoch_info(self) -> Dict[str, Any]:
        """Get epoch information including current epoch, slot index, and slots in epoch."""
        try:
            res = self.call("getEpochInfo", [{"commitment": "confirmed"}])
            return res if isinstance(res, dict) else {}
        except Exception as e:
            logger.error(f"getEpochInfo failed: {e}")
            return {}

    def get_recent_performance_samples(self, limit: int = 60) -> List[Dict[str, Any]]:
        """Get recent performance samples for TPS and slot duration estimation."""
        try:
            samples = self.call("getRecentPerformanceSamples", [limit])
            return samples if isinstance(samples, list) else []
        except Exception as e:
            logger.error(f"getRecentPerformanceSamples failed: {e}")
            return []

    def get_vote_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all active and delinquent vote accounts."""
        try:
            res = self.call("getVoteAccounts", [{"commitment": "confirmed"}])
            if isinstance(res, dict):
                return {
                    "current": res.get("current", []),
                    "delinquent": res.get("delinquent", []),
                }
            return {"current": [], "delinquent": []}
        except Exception as e:
            logger.error(f"getVoteAccounts failed: {e}")
            return {"current": [], "delinquent": []}

    def get_supply(self) -> Dict[str, Any]:
        """Get current total, circulating, and non-circulating SOL supply."""
        try:
            res = self.call("getSupply", [{"excludeNonCirculatingAccountsList": True}])
            if isinstance(res, dict) and "value" in res:
                return res["value"]
            return res if isinstance(res, dict) else {}
        except Exception as e:
            logger.error(f"getSupply failed: {e}")
            return {}

    def get_signatures_for_address(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent signatures that touched ``address`` (no API key required).

        Used by the Daily Active Address sampler to gather a real transaction
        sample that is then resolved to unique fee payers via ``get_transaction``.
        """
        try:
            res = self.call(
                "getSignaturesForAddress",
                [address, {"limit": limit, "commitment": "confirmed"}],
            )
            return res if isinstance(res, list) else []
        except Exception as e:
            logger.warning(f"getSignaturesForAddress failed for {address}: {e}")
            return []

    def get_transaction(self, signature: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Fetch a confirmed transaction and return its parsed JSON form (no API key).

        The fee payer (the account that pays and therefore the transacting
        address we count) is always ``message.accountKeys[0]``.
        """
        saved = self.timeout
        self.timeout = timeout
        try:
            res = self.call(
                "getTransaction",
                [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
            )
            return res if isinstance(res, dict) else None
        except Exception as e:
            logger.warning(f"getTransaction failed for {signature[:16]}…: {e}")
            return None
        finally:
            self.timeout = saved

    def get_recent_prioritization_fees(self, addresses: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch recent priority fee samples (lamports) to derive a measured median fee.

        Uses the native ``getRecentPrioritizationFees`` RPC call with no API keys;
        falls back to an empty list so callers can degrade to model defaults.
        """
        try:
            res = self.call("getRecentPrioritizationFees", [addresses or []])
            if isinstance(res, list):
                return res
            return []
        except Exception as e:
            logger.warning(f"getRecentPrioritizationFees failed: {e}")
            return []


if __name__ == "__main__":
    client = SolanaRPCClient()
    print("Testing RPC methods...")
    print(f"Health: {client.get_health()}")
    slot = client.get_slot()
    print(f"Current Slot: {slot}")
    if slot:
        print(f"Block Time for {slot}: {client.get_block_time(slot)}")
    epoch = client.get_epoch_info()
    print(f"Epoch Info: epoch={epoch.get('epoch')}, slotIndex={epoch.get('slotIndex')}/{epoch.get('slotsInEpoch')}")
    samples = client.get_recent_performance_samples(5)
    print(f"Sample count: {len(samples)}")
    if samples:
        first = samples[0]
        tps = first.get("numTransactions", 0) / max(1, first.get("samplePeriodSecs", 1))
        print(f"Latest sample TPS: {tps:.1f}")
    vote_accounts = client.get_vote_accounts()
    print(f"Active Validators: {len(vote_accounts.get('current', []))}")
    print(f"Delinquent Validators: {len(vote_accounts.get('delinquent', []))}")
    supply = client.get_supply()
    if supply:
        total_sol = supply.get("total", 0) / 1e9
        circ_sol = supply.get("circulating", 0) / 1e9
        print(f"Supply: Total={total_sol:,.0f} SOL, Circulating={circ_sol:,.0f} SOL")
