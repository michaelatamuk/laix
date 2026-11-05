"""Predicted and observed rates for one confidence interval."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    """Predicted and observed rates for one confidence interval."""

    lower: float
    upper: float
    predicted: float
    observed: float
    count: int


__all__ = ["CalibrationBin"]
