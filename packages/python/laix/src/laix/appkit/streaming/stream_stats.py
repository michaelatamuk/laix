"""Counters for one stream session."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StreamStats:
    """Counters for one stream session."""

    observed: int = 0
    decided: int = 0
    late: int = 0
    throttled: int = 0
    dropped: int = 0
    expired: int = 0
    suppressed: int = 0
    shed: int = 0
    duplicates: int = 0
    refine_timeouts: int = 0
    provisional: int = 0
    revised: int = 0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0

    def snapshot(self) -> dict[str, int | float]:
        return {
            "observed": self.observed,
            "decided": self.decided,
            "late": self.late,
            "throttled": self.throttled,
            "dropped": self.dropped,
            "expired": self.expired,
            "suppressed": self.suppressed,
            "shed": self.shed,
            "duplicates": self.duplicates,
            "refine_timeouts": self.refine_timeouts,
            "provisional": self.provisional,
            "revised": self.revised,
            "latency_p50": self.latency_p50,
            "latency_p95": self.latency_p95,
            "latency_p99": self.latency_p99,
        }


__all__ = ["StreamStats"]
