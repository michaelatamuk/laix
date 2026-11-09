"""A detector built from a plain function."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from ...decision.domain.perception import Detection, PerceptionEvent


@dataclass(frozen=True, slots=True)
class CallableDetector:
    """A detector from a plain function, for tests and small adapters."""

    name: str
    detect: Callable[[PerceptionEvent], Iterable[Detection]]
    tier: str = "cheap"
    cost: float = 0.0
    latency_ms: int = 0
    information_gain: float = 0.0


__all__ = ["CallableDetector"]
