"""The chance of an observation after an action and a hidden state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObservationProbability:
    """The chance of an observation after an action and a hidden state."""

    next_state: str
    action: str
    observation: str
    probability: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("observation probability must be between zero and one")


__all__ = ["ObservationProbability"]
