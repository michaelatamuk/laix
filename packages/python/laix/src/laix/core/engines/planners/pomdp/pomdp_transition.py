"""One transition in the hidden state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PomdpTransition:
    """One transition in the hidden state."""

    state: str
    action: str
    next_state: str
    probability: float = 1.0
    reward: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("transition probability must be between zero and one")


__all__ = ["PomdpTransition"]
