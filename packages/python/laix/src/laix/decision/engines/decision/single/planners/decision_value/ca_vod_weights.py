"""Weights for the commitment-attention value of decision planner."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CAVODWeights:
    """Weights for the one-step value-of-decision terms."""

    information: float = 0.5
    waiting: float = 0.25
    uncertainty: float = 0.5
    future: float = 1.0

    def __post_init__(self) -> None:
        for name in ("information", "waiting", "uncertainty", "future"):
            if getattr(self, name) < 0:
                raise ValueError(f"CA-VOD weight {name!r} must not be negative")


__all__ = ["CAVODWeights"]
