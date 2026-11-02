"""Live Context loop: run detectors under a resource budget.

The records live in :mod:`laix.core.perception`; the host supplies detectors
and drives the clock. This module runs cheap detectors always and admits deep
detectors only when gain, cost and latency allow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from ..core.values import clamp
from ..core.perception import Detection, Detector, PerceptionEvent, PerceptionFrame
from ..core.resources import Budget, ResourceScheduler, SensingOption


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
        policy: ResourceScheduler | None = None,
    ) -> None:
        self._detectors: dict[str, Detector] = {}
        self.budget = budget or Budget(max_deep_calls=2, max_cost=1.0, max_latency_ms=500)
        self.policy = policy or ResourceScheduler()
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


__all__ = ["CallableDetector", "LiveContext"]
