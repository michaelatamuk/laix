"""Live Context: continuous perception under a resource budget.

The app supplies detectors. LAIX supplies the loop, the admission rule and the
frame. Cheap detectors run on every event; a deep detector is admitted only when
its information gain, weighted by uncertainty, clears a threshold and its cost
and latency fit the budget. The default latency budget is sub-second.

This is a reference implementation. Real cameras, audio, sensors and streams are
app adapters behind the ``Detector`` protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

from ..contracts import clamp
from .resources import Budget, ResourcePolicy, SensingOption


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


@dataclass(frozen=True, slots=True)
class CallableDetector:
    """A detector from a plain function, for tests and small adapters."""

    name: str
    detect: Callable[[PerceptionEvent], Iterable[Detection]]
    tier: str = "cheap"
    cost: float = 0.0
    latency_ms: int = 0
    information_gain: float = 0.0


class LiveContext:
    """Run detectors over an event stream and return perception frames."""

    def __init__(
        self,
        detectors: Iterable[Detector] = (),
        *,
        budget: Budget | None = None,
        policy: ResourcePolicy | None = None,
    ) -> None:
        self._detectors: dict[str, Detector] = {}
        self.budget = budget or Budget(max_deep_calls=2, max_cost=1.0, max_latency_ms=500)
        self.policy = policy or ResourcePolicy()
        self.frames: list[PerceptionFrame] = []
        for detector in detectors:
            self.register(detector)

    def register(self, detector: Detector) -> None:
        name = detector.name.strip()
        if not name:
            raise ValueError("detector name is required")
        if not callable(getattr(detector, "detect", None)):
            raise ValueError(f"detector {name!r} has no detect method")
        self._detectors[name] = detector

    def detectors(self) -> tuple[str, ...]:
        return tuple(self._detectors)

    def perceive(
        self,
        event: PerceptionEvent,
        *,
        uncertainty: float = 0.5,
    ) -> PerceptionFrame:
        uncertainty = clamp(uncertainty)
        options = [
            SensingOption(
                name=detector.name,
                tier=detector.tier,
                cost=detector.cost,
                latency_ms=detector.latency_ms,
                information_gain=detector.information_gain,
            )
            for detector in self._detectors.values()
        ]
        plan = self.policy.schedule(options, budget=self.budget, uncertainty=uncertainty)

        detections: list[Detection] = []
        remaining = uncertainty
        for name in plan.allowed:
            found = tuple(self._detectors[name].detect(event))
            detections.extend(found)
            if found:
                best = max(item.confidence for item in found)
                gain = self._detectors[name].information_gain * best
                remaining *= 1.0 - min(0.98, gain)

        frame = PerceptionFrame(
            subject=event.subject,
            at=event.at,
            detections=tuple(detections),
            allowed=plan.allowed,
            skipped=plan.skipped,
            uncertainty=clamp(remaining),
            deep_calls=plan.deep_calls,
            cost=plan.cost,
        )
        self.frames.append(frame)
        return frame

    def feed(
        self,
        events: Iterable[PerceptionEvent],
        *,
        uncertainty: float = 0.5,
    ) -> tuple[PerceptionFrame, ...]:
        return tuple(self.perceive(event, uncertainty=uncertainty) for event in events)

    @property
    def latest(self) -> PerceptionFrame | None:
        return self.frames[-1] if self.frames else None


__all__ = [
    "CallableDetector",
    "Detection",
    "Detector",
    "LiveContext",
    "PerceptionEvent",
    "PerceptionFrame",
]
