"""Weights for the commitment-aware planner."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommitmentWeights:
    """How much each commitment effect changes the utility score."""

    keep: float = 0.35
    violate: float = 1.0
    create: float = 0.10
    due: float = 0.25
    blocked: float = 0.50

    def __post_init__(self) -> None:
        for name in ("keep", "violate", "create", "due", "blocked"):
            if getattr(self, name) < 0:
                raise ValueError(f"commitment weight {name!r} must not be negative")


__all__ = ["CommitmentWeights"]
