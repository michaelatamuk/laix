"""Weights for the attention-aware planner."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HumanAttentionWeights:
    """How much each kind of human attention costs."""

    interrupt: float = 0.4
    approval: float = 0.25
    escalation: float = 0.3
    exhausted: float = 1.0

    def __post_init__(self) -> None:
        for name in ("interrupt", "approval", "escalation", "exhausted"):
            if getattr(self, name) < 0:
                raise ValueError(f"attention weight {name!r} must not be negative")


__all__ = ["HumanAttentionWeights"]
