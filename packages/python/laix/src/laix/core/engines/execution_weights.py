"""Weights for the execution-aware planner."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionWeights:
    """How much each execution risk subtracts from the utility score."""

    irreversible: float = 0.35
    unknown: float = 0.5
    approval: float = 0.15
    recovery: float = 0.25

    def __post_init__(self) -> None:
        for name in ("irreversible", "unknown", "approval", "recovery"):
            if getattr(self, name) < 0:
                raise ValueError(f"execution weight {name!r} must not be negative")


__all__ = ["ExecutionWeights"]
