"""
Multi-endpoint RPC orchestrator for Solana with consensus voting and failover.

Implements 3-endpoint consensus (Helius, Triton, Solana Foundation) with 2/3
majority voting for critical metrics. Gracefully falls back to 2 endpoints
if one fails, and tracks endpoint health for observability.
"""

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from collector.rpc import SolanaRPCClient


@dataclass
class EndpointHealth:
    """Tracks health of a single RPC endpoint."""
    name: str
    url: str
    last_success: Optional[float] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def is_healthy(self, max_consecutive_failures: int = 3) -> bool:
        """Endpoint is healthy if it hasn't exceeded failure threshold."""
        return self.consecutive_failures < max_consecutive_failures
    
    def mark_success(self):
        """Record successful request."""
        self.last_success = time.time()
        self.last_error = None
        self.consecutive_failures = 0
        self.success_count += 1
    
    def mark_failure(self, error: str):
        """Record failed request."""
        self.last_error = error
        self.consecutive_failures += 1
        self.failure_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Export health data for reporting."""
        return {
            "name": self.name,
            "healthy": self.is_healthy(),
            "last_success": self.last_success,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


@dataclass
class ConsensusResult:
    """Result of a consensus voting round."""
    metric: str
    agreed_value: Any
    voting_round: Dict[str, Any]
    consensus_achieved: bool
    healthy_endpoints: int
    required_endpoints: int
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export consensus result."""
        return {
            "metric": self.metric,
            "agreed_value": self.agreed_value,
            "consensus_achieved": self.consensus_achieved,
            "healthy_endpoints": self.healthy_endpoints,
            "required_endpoints": self.required_endpoints,
            "timestamp": self.timestamp,
        }


class RpcOrchestrator:
    """
    Multi-endpoint RPC orchestrator with consensus voting.
    
    Queries 3 Solana RPC endpoints and uses 2/3 majority voting to determine
    authoritative values for critical metrics. Falls back to 2 endpoints if
    one fails, and tracks endpoint health for observability.
    """
    
    # Default endpoints (can be overridden)
    DEFAULT_ENDPOINTS = [
        ("Solana Foundation", "https://api.mainnet-beta.solana.com/"),
    ]

    # Users can add paid RPC endpoints for true multi-endpoint consensus:
    # ("Helius", "https://mainnet.helius-rpc.com/?api-key=YOUR_KEY"),
    # ("Triton", "https://api.mainnet.solana.rpc.triton.one/YOUR_KEY"),
    # ("QuickNode", "https://your-endpoint.quiknode.pro/YOUR_KEY"),
    
    # Critical metrics for consensus voting
    CRITICAL_METRICS = {
        "getSlot",
        "getEpochInfo",
        "getRecentPerformanceSamples",
        "getVoteAccounts",
        "getSupply",
    }
    
    def __init__(self, endpoints: Optional[List[tuple]] = None):
        """Initialize orchestrator with RPC endpoints."""
        self.endpoints_config = endpoints or self.DEFAULT_ENDPOINTS
        self.endpoints: List[SolanaRPCClient] = []
        self.health: Dict[str, EndpointHealth] = {}
        self.consensus_votes: List[ConsensusResult] = []
        
        # Initialize endpoint clients and health trackers
        for name, url in self.endpoints_config:
            client = SolanaRPCClient(url)
            self.endpoints.append(client)
            self.health[name] = EndpointHealth(name=name, url=url)
    
    def _query_endpoint(self, endpoint: SolanaRPCClient, method: str, params: List[Any] = None) -> Optional[Any]:
        """Query a single endpoint with error handling."""
        try:
            # Build JSON-RPC request
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or [],
            }
            
            # Execute request
            response = endpoint.call(method, params or [])
            return response
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
            return None
    
    def _majority_vote(self, results: Dict[str, Any], metric_name: str) -> ConsensusResult:
        """Determine majority value using 2/3 voting."""
        # Filter healthy endpoints
        healthy_results = {k: v for k, v in results.items() if v is not None}
        
        if not healthy_results:
            # All endpoints failed
            return ConsensusResult(
                metric=metric_name,
                agreed_value=None,
                voting_round=results,
                consensus_achieved=False,
                healthy_endpoints=0,
                required_endpoints=2,
            )
        
        # Count occurrences of each value (convert to JSON for comparison)
        value_counts: Dict[str, int] = {}
        value_map: Dict[str, Any] = {}
        
        for endpoint_name, value in healthy_results.items():
            # Serialize for comparison (handles various types)
            if isinstance(value, (dict, list)):
                key = json.dumps(value, sort_keys=True, default=str)
            else:
                key = str(value)
            
            value_counts[key] = value_counts.get(key, 0) + 1
            value_map[key] = value
        
        # Find majority (2/3 = at least 2 out of 3 healthy endpoints)
        consensus_threshold = max(1, len(healthy_results) // 2 + 1)
        consensus_achieved = False
        agreed_value = None
        
        for key, count in value_counts.items():
            if count >= consensus_threshold:
                consensus_achieved = True
                agreed_value = value_map[key]
                break
        
        # If no consensus, use most common value
        if not consensus_achieved and value_counts:
            most_common_key = max(value_counts, key=value_counts.get)
            agreed_value = value_map[most_common_key]
        
        return ConsensusResult(
            metric=metric_name,
            agreed_value=agreed_value,
            voting_round=results,
            consensus_achieved=consensus_achieved,
            healthy_endpoints=len(healthy_results),
            required_endpoints=consensus_threshold,
        )
    
    def get_slot_with_consensus(self) -> Optional[int]:
        """Get current slot with 2/3 consensus voting."""
        results = {}
        
        for i, endpoint in enumerate(self.endpoints):
            endpoint_name = self.endpoints_config[i][0]
            health = self.health[endpoint_name]
            
            if not health.is_healthy():
                results[endpoint_name] = None
                continue
            
            try:
                slot = self._query_endpoint(endpoint, "getSlot", [])
                if slot is not None:
                    health.mark_success()
                    results[endpoint_name] = slot
                else:
                    health.mark_failure("Invalid response")
                    results[endpoint_name] = None
            except Exception as e:
                health.mark_failure(str(e))
                results[endpoint_name] = None
        
        consensus = self._majority_vote(results, "getSlot")
        self.consensus_votes.append(consensus)
        return consensus.agreed_value
    
    def get_epoch_info_with_consensus(self) -> Optional[Dict[str, Any]]:
        """Get epoch info with 2/3 consensus voting."""
        results = {}
        
        for i, endpoint in enumerate(self.endpoints):
            endpoint_name = self.endpoints_config[i][0]
            health = self.health[endpoint_name]
            
            if not health.is_healthy():
                results[endpoint_name] = None
                continue
            
            try:
                epoch_info = self._query_endpoint(endpoint, "getEpochInfo", [])
                if epoch_info is not None:
                    health.mark_success()
                    results[endpoint_name] = epoch_info
                else:
                    health.mark_failure("Invalid response")
                    results[endpoint_name] = None
            except Exception as e:
                health.mark_failure(str(e))
                results[endpoint_name] = None
        
        consensus = self._majority_vote(results, "getEpochInfo")
        self.consensus_votes.append(consensus)
        return consensus.agreed_value
    
    def get_vote_accounts_with_consensus(self) -> Optional[Dict[str, Any]]:
        """Get vote accounts with 2/3 consensus voting."""
        results = {}
        
        for i, endpoint in enumerate(self.endpoints):
            endpoint_name = self.endpoints_config[i][0]
            health = self.health[endpoint_name]
            
            if not health.is_healthy():
                results[endpoint_name] = None
                continue
            
            try:
                vote_accts = self._query_endpoint(endpoint, "getVoteAccounts", [])
                if vote_accts is not None:
                    health.mark_success()
                    results[endpoint_name] = vote_accts
                else:
                    health.mark_failure("Invalid response")
                    results[endpoint_name] = None
            except Exception as e:
                health.mark_failure(str(e))
                results[endpoint_name] = None
        
        consensus = self._majority_vote(results, "getVoteAccounts")
        self.consensus_votes.append(consensus)
        return consensus.agreed_value

    def get_health_with_consensus(self) -> Optional[str]:
        """Get cluster health with 2/3 consensus voting.
        
        Returns 'ok' if majority of healthy endpoints report healthy,
        otherwise returns the first non-ok response or 'degraded'.
        """
        results = {}
        
        for i, endpoint in enumerate(self.endpoints):
            endpoint_name = self.endpoints_config[i][0]
            health = self.health[endpoint_name]
            
            if not health.is_healthy():
                results[endpoint_name] = None
                continue
            
            try:
                health_result = self._query_endpoint(endpoint, "getHealth", [])
                if health_result is not None:
                    health.mark_success()
                    results[endpoint_name] = health_result if isinstance(health_result, str) else str(health_result)
                else:
                    health.mark_failure("Invalid response")
                    results[endpoint_name] = None
            except Exception as e:
                health.mark_failure(str(e))
                results[endpoint_name] = None
        
        # For health, use majority voting — if 2+ endpoints say 'ok', cluster is healthy
        consensus = self._majority_vote(results, "getHealth")
        self.consensus_votes.append(consensus)
        return consensus.agreed_value if consensus.agreed_value else "degraded"

    def get_supply_with_consensus(self) -> Optional[Dict[str, Any]]:
        """Get supply info with 2/3 consensus voting."""
        results = {}
        
        for i, endpoint in enumerate(self.endpoints):
            endpoint_name = self.endpoints_config[i][0]
            health = self.health[endpoint_name]
            
            if not health.is_healthy():
                results[endpoint_name] = None
                continue
            
            try:
                supply = self._query_endpoint(endpoint, "getSupply",
                    [{"excludeNonCirculatingAccountsList": True}])
                if supply is not None:
                    health.mark_success()
                    # Extract value dict if wrapped
                    if isinstance(supply, dict) and "value" in supply:
                        results[endpoint_name] = supply["value"]
                    else:
                        results[endpoint_name] = supply
                else:
                    health.mark_failure("Invalid response")
                    results[endpoint_name] = None
            except Exception as e:
                health.mark_failure(str(e))
                results[endpoint_name] = None
        
        consensus = self._majority_vote(results, "getSupply")
        self.consensus_votes.append(consensus)
        return consensus.agreed_value

    def get_performance_samples_with_consensus(self, limit: int = 30) -> Optional[list]:
        """Get recent performance samples with 2/3 consensus voting."""
        results = {}
        
        for i, endpoint in enumerate(self.endpoints):
            endpoint_name = self.endpoints_config[i][0]
            health = self.health[endpoint_name]
            
            if not health.is_healthy():
                results[endpoint_name] = None
                continue
            
            try:
                samples = self._query_endpoint(endpoint, "getRecentPerformanceSamples", [limit])
                if samples is not None and isinstance(samples, list):
                    health.mark_success()
                    results[endpoint_name] = samples
                else:
                    health.mark_failure("Invalid response")
                    results[endpoint_name] = None
            except Exception as e:
                health.mark_failure(str(e))
                results[endpoint_name] = None
        
        consensus = self._majority_vote(results, "getRecentPerformanceSamples")
        self.consensus_votes.append(consensus)
        return consensus.agreed_value
    
    def get_health_status(self) -> Dict[str, Any]:
        """Export health status of all endpoints."""
        return {
            endpoint_name: health.to_dict()
            for endpoint_name, health in self.health.items()
        }
    
    def get_consensus_stats(self) -> Dict[str, Any]:
        """Export consensus voting statistics."""
        total_votes = len(self.consensus_votes)
        consensus_achieved = sum(1 for v in self.consensus_votes if v.consensus_achieved)
        
        return {
            "total_consensus_rounds": total_votes,
            "consensus_achieved_count": consensus_achieved,
            "consensus_achieved_pct": (consensus_achieved / total_votes * 100) if total_votes > 0 else 0,
            "avg_healthy_endpoints": (
                sum(v.healthy_endpoints for v in self.consensus_votes) / total_votes
                if total_votes > 0 else 0
            ),
            "recent_votes": [v.to_dict() for v in self.consensus_votes[-10:]],
        }
    
    def to_report_dict(self) -> Dict[str, Any]:
        """Export orchestrator status for reporting."""
        return {
            "rpc_orchestrator": {
                "active_endpoints": len(self.endpoints_config),
                "endpoint_health": self.get_health_status(),
                "consensus_stats": self.get_consensus_stats(),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }
