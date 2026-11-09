"""One step in a simulated trace."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationStep:
    """One step in a simulated trace."""

    step: int
    state: str
    action: str | None
    reward: float
    next_state: str


__all__ = ["SimulationStep"]
