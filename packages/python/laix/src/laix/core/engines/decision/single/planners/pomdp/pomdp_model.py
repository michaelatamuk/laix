"""A finite POMDP with discrete states, actions and observations."""

from __future__ import annotations

from dataclasses import dataclass

from .observation_probability import ObservationProbability
from .pomdp_transition import PomdpTransition


@dataclass(frozen=True, slots=True)
class PomdpModel:
    """A finite POMDP with discrete states, actions and observations."""

    states: tuple[str, ...]
    actions: tuple[str, ...]
    observations: tuple[str, ...]
    transitions: tuple[PomdpTransition, ...]
    observation_table: tuple[ObservationProbability, ...]
    discount: float = 0.9
    horizon: int = 3

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("a POMDP needs at least one state")
        if not self.actions:
            raise ValueError("a POMDP needs at least one action")
        if not self.observations:
            raise ValueError("a POMDP needs at least one observation")
        if len(set(self.states)) != len(self.states):
            raise ValueError("POMDP states must be unique")
        if len(set(self.actions)) != len(self.actions):
            raise ValueError("POMDP actions must be unique")
        if len(set(self.observations)) != len(self.observations):
            raise ValueError("POMDP observations must be unique")
        if not 0.0 <= self.discount <= 1.0:
            raise ValueError("discount must be between zero and one")
        if self.horizon < 0:
            raise ValueError("horizon must not be negative")
        states = set(self.states)
        actions = set(self.actions)
        observations = set(self.observations)
        for item in self.transitions:
            if item.state not in states or item.next_state not in states:
                raise ValueError(f"transition refers to an unknown state: {item}")
            if item.action not in actions:
                raise ValueError(f"transition refers to an unknown action: {item}")
        for item in self.observation_table:
            if item.next_state not in states:
                raise ValueError(f"observation refers to an unknown state: {item}")
            if item.action not in actions:
                raise ValueError(f"observation refers to an unknown action: {item}")
            if item.observation not in observations:
                raise ValueError(f"unknown observation: {item}")

        for state in self.states:
            for action in self.actions:
                rows = self.transition_rows(state, action)
                if rows:
                    total = sum(item.probability for item in rows)
                    if abs(total - 1.0) > 1e-6:
                        raise ValueError(
                            f"transitions for {state!r}/{action!r} sum to {total:.6f}"
                        )
        reachable = {
            (item.next_state, item.action)
            for item in self.transitions
            if item.probability > 0
        }
        for next_state, action in sorted(reachable):
            rows = self.observation_rows(next_state, action)
            if not rows:
                raise ValueError(
                    f"missing observations for {next_state!r}/{action!r}"
                )
            total = sum(item.probability for item in rows)
            if abs(total - 1.0) > 1e-6:
                raise ValueError(
                    f"observations for {next_state!r}/{action!r} "
                    f"sum to {total:.6f}"
                )

    def transition_rows(
        self,
        state: str,
        action: str,
    ) -> tuple[PomdpTransition, ...]:
        return tuple(
            item
            for item in self.transitions
            if item.state == state and item.action == action
        )

    def observation_rows(
        self,
        next_state: str,
        action: str,
    ) -> tuple[ObservationProbability, ...]:
        return tuple(
            item
            for item in self.observation_table
            if item.next_state == next_state and item.action == action
        )

    def action_available(self, state: str, action: str) -> bool:
        return bool(self.transition_rows(state, action))


__all__ = ["PomdpModel"]
