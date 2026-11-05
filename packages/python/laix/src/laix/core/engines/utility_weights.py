"""How much each cost subtracts from expected benefit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UtilityWeights:
    """How much each cost subtracts from expected benefit."""

    benefit: float = 1.0
    cost: float = 0.25
    risk: float = 0.25
    interruption: float = 0.15
    latency: float = 0.0

    def __post_init__(self) -> None:
        for name in ("benefit", "cost", "risk", "interruption", "latency"):
            if getattr(self, name) < 0:
                raise ValueError(f"utility weight {name!r} must not be negative")


__all__ = ["UtilityWeights"]
