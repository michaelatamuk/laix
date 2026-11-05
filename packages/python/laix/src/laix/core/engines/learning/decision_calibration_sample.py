"""One decision and whether it turned out to be correct."""

from __future__ import annotations

from dataclasses import dataclass

from ...support.values import clamp


@dataclass(frozen=True, slots=True)
class DecisionCalibrationSample:
    """One decision and whether it turned out to be correct."""

    confidence: float
    correct: bool
    verb: str = ""
    action_id: str = ""
    policy: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", clamp(self.confidence))


__all__ = ["DecisionCalibrationSample"]
