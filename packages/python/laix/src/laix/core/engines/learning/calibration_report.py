"""A reliability summary for one policy or one sample set."""

from __future__ import annotations

from dataclasses import dataclass

from ...support.values import clamp
from .calibration_bin import CalibrationBin


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    """A reliability summary for one policy or one sample set."""

    samples: int
    accuracy: float
    expected: float
    error: float
    bins: tuple[CalibrationBin, ...]
    policy: str = ""
    smoothing: float = 0.0

    def adjust(self, confidence: float) -> float:
        """Map one confidence value onto the observed rate."""
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
        }


__all__ = ["CalibrationReport"]
