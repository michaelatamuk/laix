"""A finite, discrete MDP."""

from __future__ import annotations

from dataclasses import dataclass

from .mdp_transition import MdpTransition


@dataclass(frozen=True, slots=True)
class MdpModel:
    """A finite, discrete MDP."""

    states: tuple[str, ...]
    actions: tuple[str, ...]
    transitions: tuple[MdpTransition, ...]
    start: str
    discount: float = 0.9
    horizon: int | None = 20

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("an MDP needs at least one state")
        if len(set(self.states)) != len(self.states):
            raise ValueError("MDP states must be unique")
        if len(set(self.actions)) != len(self.actions):
            raise ValueError("MDP actions must be unique")
        if self.start not in self.states:
            raise ValueError(f"unknown start state: {self.start!r}")
        if not 0.0 <= self.discount <= 1.0:
            raise ValueError("discount must be between zero and one")
        if self.horizon is not None and self.horizon < 0:
            raise ValueError("horizon must not be negative")
        known_states = set(self.states)
        known_actions = set(self.actions)
        for item in self.transitions:
            if item.state not in known_states or item.next_state not in known_states:
                raise ValueError(f"transition refers to an unknown state: {item}")
            if item.action not in known_actions:
                raise ValueError(f"transition refers to an unknown action: {item}")
        for state in self.states:
            for action in self.actions:
                rows = self.outgoing(state, action)
                if rows:
                    total = sum(item.probability for item in rows)
                    if abs(total - 1.0) > 1e-6:
                        raise ValueError(
                            f"transitions for {state!r}/{action!r} sum to {total:.6f}"
                        )

    def outgoing(self, state: str, action: str) -> tuple[MdpTransition, ...]:
        return tuple(
            item
            for item in self.transitions
            if item.state == state and item.action == action
        )

    def actions_for(self, state: str) -> tuple[str, ...]:
        return tuple(
            action
            for action in self.actions
            if self.outgoing(state, action)
        )


__all__ = ["MdpModel"]
