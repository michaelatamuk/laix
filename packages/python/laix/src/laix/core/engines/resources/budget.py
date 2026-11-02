"""Resource limits for perception and model calls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    max_deep_calls: int = 4
    max_cost: float = 1.0
    max_latency_ms: int = 2_000


__all__ = ["Budget"]
