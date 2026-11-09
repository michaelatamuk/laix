"""Decision-level calibration report."""

from __future__ import annotations

from dataclasses import dataclass

from ...support.values import clamp
from .calibration import CalibrationBin


@dataclass(frozen=True, slots=True)
class DecisionCalibrationReport:
    """A reliability summary for decisions, with per-verb and per-action accuracy."""

    samples: int
    accuracy: float
    expected: float
    error: float
    bins: tuple[CalibrationBin, ...]
    verb_accuracy: dict[str, float]
    action_accuracy: dict[str, float]
    policy: str = ""
    smoothing: float = 0.0

    def adjust(self, confidence: float) -> float:
        """Map one confidence value onto the observed decision rate."""
        for item in self.bins:
            if item.count and item.lower <= confidence < item.upper:
                return clamp(item.observed)
            if item.count and confidence == 1.0 and item.upper == 1.0:
                return clamp(item.observed)
        return clamp(confidence - (self.expected - self.accuracy))

    def to_dict(self) -> dict[str, object]:
        return {
            "samples": self.samples,
            "accuracy": self.accuracy,
            "expected": self.expected,
            "error": self.error,
            "policy": self.policy,
            "smoothing": self.smoothing,
            "bins": [
                {
                    "lower": item.lower,
                    "upper": item.upper,
                    "predicted": item.predicted,
                    "observed": item.observed,
                    "count": item.count,
                }
                for item in self.bins
            ],
            "verb_accuracy": dict(self.verb_accuracy),
            "action_accuracy": dict(self.action_accuracy),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DecisionCalibrationReport":
        bins = tuple(
            CalibrationBin(**item)
            for item in payload.get("bins", ())
            if isinstance(item, dict)
        )
        return cls(
            samples=int(payload.get("samples", 0)),
            accuracy=float(payload.get("accuracy", 0.0)),
            expected=float(payload.get("expected", 0.0)),
            error=float(payload.get("error", 0.0)),
            bins=bins,
            verb_accuracy=dict(payload.get("verb_accuracy", {})),
            action_accuracy=dict(payload.get("action_accuracy", {})),
            policy=str(payload.get("policy", "")),
            smoothing=float(payload.get("smoothing", 0.0)),
        )


__all__ = ["DecisionCalibrationReport"]
