"""The execution facts that change an option's score."""

from __future__ import annotations

from dataclasses import dataclass

from ..support.values import clamp


@dataclass(frozen=True, slots=True)
class ExecutionEffect:
    """The execution facts that change an option's score."""

    unknown_risk: float = 0.0
    recovery_cost: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "unknown_risk", clamp(self.unknown_risk))
        object.__setattr__(self, "recovery_cost", max(0.0, float(self.recovery_cost)))


__all__ = ["ExecutionEffect"]
