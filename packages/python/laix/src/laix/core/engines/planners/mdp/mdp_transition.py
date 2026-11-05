"""One probabilistic transition from a state under an action."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MdpTransition:
    """One probabilistic transition from a state under an action."""

    state: str
    action: str
    next_state: str
    probability: float = 1.0
    reward: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("transition probability must be between zero and one")


__all__ = ["MdpTransition"]
