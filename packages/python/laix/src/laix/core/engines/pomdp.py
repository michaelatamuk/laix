"""A small finite POMDP: belief update and finite-horizon expectimax.

This is a reference implementation for small models. It makes the belief and
the observation model explicit, which is more useful than a large solver that
hides its assumptions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ..support.values import clamp
from .engine import DecisionProblem, Plan
from .mdp import MdpModel, value_iteration


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


def normalize_belief(
    belief: Mapping[str, float],
    states: Iterable[str],
) -> dict[str, float]:
    """Clamp, drop unknowns and renormalise one belief."""
    allowed = set(states)
    clean = {
        state: max(0.0, float(probability))
        for state, probability in belief.items()
        if state in allowed
    }
    total = sum(clean.values())
    if total <= 0:
        size = max(1, len(allowed))
        return {state: 1.0 / size for state in allowed}
    return {state: round(probability / total, 9) for state, probability in clean.items()}


def belief_from_state(state: str, states: Iterable[str]) -> dict[str, float]:
    """Put all belief on one state."""
    space = tuple(states)
    if state not in space:
        raise ValueError(f"unknown state: {state!r}")
    return {item: 1.0 if item == state else 0.0 for item in space}


def belief_update(
    model: PomdpModel,
    belief: Mapping[str, float],
    action: str,
    observation: str,
) -> dict[str, float]:
    """Bayes update after one action and one observation."""
    current = normalize_belief(belief, model.states)
    predicted: dict[str, float] = {}
    for next_state in model.states:
        probability = sum(
            current.get(state, 0.0) * item.probability
            for state in model.states
            for item in model.transition_rows(state, action)
            if item.next_state == next_state
        )
        if probability:
            predicted[next_state] = probability
    if not predicted:
        return dict(current)

    likelihood = {
        next_state: next(
            (
                item.probability
                for item in model.observation_rows(next_state, action)
                if item.observation == observation
            ),
            0.0,
        )
        for next_state in predicted
    }
    unnormalised = {
        next_state: predicted[next_state] * likelihood[next_state]
        for next_state in predicted
    }
    total = sum(unnormalised.values())
    if total <= 0:
        return normalize_belief(predicted, model.states)
    return {
        next_state: round(probability / total, 9)
        for next_state, probability in unnormalised.items()
    }


def observation_probability(
    model: PomdpModel,
    belief: Mapping[str, float],
    action: str,
    observation: str,
) -> float:
    """P(observation | belief, action)."""
    current = normalize_belief(belief, model.states)
    total = 0.0
    for next_state in model.states:
        transition = sum(
            current.get(state, 0.0) * item.probability
            for state in model.states
            for item in model.transition_rows(state, action)
            if item.next_state == next_state
        )
        chance = next(
            (
                item.probability
                for item in model.observation_rows(next_state, action)
                if item.observation == observation
            ),
            0.0,
        )
        total += transition * chance
    return total


def belief_entropy(belief: Mapping[str, float]) -> float:
    """Shannon entropy, in bits, of one belief."""
    total = sum(belief.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for probability in belief.values():
        value = probability / total
        if value > 0:
            entropy -= value * math.log2(value)
    return round(entropy, 6)


def _immediate_reward(
    model: PomdpModel,
    belief: Mapping[str, float],
    action: str,
) -> float:
    return sum(
        belief.get(state, 0.0) * item.probability * item.reward
        for state in model.states
        for item in model.transition_rows(state, action)
    )


def _action_value(
    model: PomdpModel,
    belief: Mapping[str, float],
    action: str,
    depth: int,
    cache: dict[tuple[tuple[tuple[str, float], ...], str, int], float],
) -> float:
    key = (tuple(sorted(belief.items())), action, depth)
    if key in cache:
        return cache[key]
    value = _immediate_reward(model, belief, action)
    if depth > 0:
        future = 0.0
        for observation in model.observations:
            chance = observation_probability(model, belief, action, observation)
            if chance <= 0:
                continue
            updated = belief_update(model, belief, action, observation)
            future += chance * _best_value(model, updated, depth - 1, cache)
        value += model.discount * future
    cache[key] = value
    return value


def _best_value(
    model: PomdpModel,
    belief: Mapping[str, float],
    depth: int,
    cache: dict[tuple[tuple[tuple[str, float], ...], str, int], float],
) -> float:
    if depth < 0:
        return 0.0
    actions = [
        action
        for action in model.actions
        if any(model.action_available(state, action) for state in belief)
    ]
    if not actions:
        return 0.0
    return max(
        _action_value(model, belief, action, depth, cache)
        for action in actions
    )


def pomdp_value(
    model: PomdpModel,
    belief: Mapping[str, float],
    *,
    horizon: int | None = None,
) -> float:
    """Best expected value of a belief over a finite horizon."""
    resolved = normalize_belief(belief, model.states)
    steps = model.horizon if horizon is None else horizon
    if steps <= 0:
        return 0.0
    return round(_best_value(model, resolved, steps - 1, {}), 6)


@dataclass(frozen=True, slots=True)
class PlannerComparison:
    """A sanity check between a POMDP belief and its most likely MDP state."""

    pomdp: float
    mdp: float
    gap: float
    state: str


def compare_pomdp_to_mdp(
    pomdp: PomdpModel,
    mdp: MdpModel,
    belief: Mapping[str, float],
    *,
    horizon: int | None = None,
) -> PlannerComparison:
    """Compare the belief value with the MDP value of the most likely state.

    This is a diagnostic, not an optimality proof: a POMDP can be worth less
    than the fully observable MDP because uncertainty is real.
    """
    resolved = normalize_belief(belief, pomdp.states)
    state = max(resolved, key=lambda item: (resolved[item], item))
    pomdp_score = pomdp_value(pomdp, resolved, horizon=horizon)
    mdp_score = round(value_iteration(mdp)[state], 6)
    return PlannerComparison(
        pomdp=pomdp_score,
        mdp=mdp_score,
        gap=round(abs(pomdp_score - mdp_score), 6),
        state=state,
    )


class POMDPEngine:
    """Choose the action with the highest belief-state value."""

    name = "pomdp.v1"

    def __init__(self, model: PomdpModel, *, belief: Mapping[str, float] | None = None) -> None:
        self.model = model
        self.belief = dict(belief or {})
        self.version = self.name

    def solve(self, problem: DecisionProblem) -> Plan:
        attributes = problem.attributes
        belief = self._resolve_belief(attributes)
        horizon = int(attributes.get("horizon", self.model.horizon))
        depth = max(-1, horizon - 1)
        cache: dict[tuple[tuple[tuple[str, float], ...], str, int], float] = {}
        rows = sorted(
            (
                (
                    action,
                    round(
                        _action_value(self.model, belief, action, depth, cache),
                        6,
                    ),
                )
                for action in self.model.actions
                if any(self.model.action_available(state, action) for state in belief)
            ),
            key=lambda item: (-item[1], item[0]),
        )
        if not rows:
            return Plan(
                verb="wait",
                confidence=1.0,
                reason_code="no_action",
                rationale="no action is available under the current belief",
                score=0.0,
            )

        best_action, best_value = rows[0]
        second = rows[1][1] if len(rows) > 1 else None
        return Plan(
            verb="act",
            confidence=self._confidence(best_value, second),
            reason_code="pomdp_plan",
            rationale=(
                f"{best_action} has the highest expected value {best_value:.3f} "
                "under the current belief"
            ),
            action_id=best_action,
            score=best_value,
            alternatives=tuple(
                {
                    "action_id": action,
                    "value": value,
                    "rejected_because": "lower expected value",
                }
                for action, value in rows[1:]
            ),
            attributes={
                "belief": belief,
                "entropy": belief_entropy(belief),
                "horizon": horizon,
            },
        )

    def _resolve_belief(self, attributes: Mapping[str, Any]) -> dict[str, float]:
        value = attributes.get("belief")
        if isinstance(value, Mapping):
            return normalize_belief(value, self.model.states)
        if self.belief:
            return normalize_belief(self.belief, self.model.states)
        state = attributes.get("state")
        if isinstance(state, str) and state:
            return belief_from_state(state, self.model.states)
        size = len(self.model.states)
        return {state: 1.0 / size for state in self.model.states}

    @staticmethod
    def _confidence(best: float, second: float | None) -> float:
        if second is None:
            return 1.0
        gap = max(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / max(abs(best), 1e-9)))


__all__ = [
    "ObservationProbability",
    "POMDPEngine",
    "PlannerComparison",
    "PomdpModel",
    "PomdpTransition",
    "belief_entropy",
    "belief_from_state",
    "belief_update",
    "compare_pomdp_to_mdp",
    "normalize_belief",
    "observation_probability",
    "pomdp_value",
]
