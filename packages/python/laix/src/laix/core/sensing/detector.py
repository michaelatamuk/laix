"""A cheap or deep detector the app supplies."""

from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from .detection import Detection
from .event import PerceptionEvent


@runtime_checkable
class Detector(Protocol):
    """A cheap or deep detector the app supplies."""

    name: str
    tier: str
    cost: float
    latency_ms: int
    information_gain: float

    def detect(self, event: PerceptionEvent) -> Iterable[Detection]:
        ...


__all__ = ["Detector"]
