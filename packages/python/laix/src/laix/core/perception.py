"""Perception contracts: detectors, detections and frames.

The contracts are part of the decision vocabulary. The host supplies detectors
and drives the clock; the runtime loop lives in ``laix.appkit.live_context``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, runtime_checkable

from .contracts import clamp


@dataclass(frozen=True, slots=True)
class Detection:
    """One thing a detector noticed in one event."""

    id: str
    detector: str
    kind: str
    subject: str
    at: str
    confidence: float = 0.5
    severity: str = "low"
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", clamp(self.confidence))

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


@dataclass(frozen=True, slots=True)
class PerceptionEvent:
    """One input to the loop: what happened, when and where."""

    subject: str
    at: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PerceptionFrame:
    """What the loop saw for one event and what it skipped."""

    subject: str
    at: str
    detections: tuple[Detection, ...]
    allowed: tuple[str, ...]
    skipped: tuple[dict[str, Any], ...]
    uncertainty: float
    deep_calls: int = 0
    cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "at": self.at,
            "detections": [item.to_dict() for item in self.detections],
            "allowed": list(self.allowed),
            "skipped": [dict(item) for item in self.skipped],
            "uncertainty": round(self.uncertainty, 6),
            "deepCalls": self.deep_calls,
            "cost": round(self.cost, 6),
        }


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


__all__ = ["Detection", "Detector", "PerceptionEvent", "PerceptionFrame"]
