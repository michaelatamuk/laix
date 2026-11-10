"""A small finite MDP planner with value iteration.

The app supplies the states, actions, transitions and rewards. The planner
returns the best action for one state, with the expected value and the
alternatives, so the result is explainable.
"""

from __future__ import annotations

from dataclasses import dataclass

from ....support.values import clamp
from ....contract.planner_policy import PlannerInput, PlannerResult
from .mdp_model import MdpModel
from .mdp_transition import MdpTransition


def _q_value(
    model: MdpModel,
    state: str,
    action: str,
    values: dict[str, float],
) -> float:
    return sum(
        item.probability * (item.reward + model.discount * values[item.next_state])
        for item in model.outgoing(state, action)
    )


def value_iteration(
    model: MdpModel,
    *,
    horizon: int | None = None,
    tolerance: float = 1e-9,
    max_iterations: int = 1000,
) -> dict[str, float]:
    """Return the value of every state under a finite or infinite horizon.

    ``horizon`` overrides the model's horizon. A horizon of zero means no
    lookahead: every state is worth zero.
    """
    values = {state: 0.0 for state in model.states}
    limit = model.horizon if horizon is None else horizon
    if limit is not None and limit <= 0:
        return values
    iterations = limit if limit is not None else max_iterations
    for _ in range(iterations):
        updated: dict[str, float] = {}
        delta = 0.0
        for state in model.states:
            actions = model.actions_for(state)
            if not actions:
                updated[state] = 0.0
                continue
            value = max(_q_value(model, state, action, values) for action in actions)
            updated[state] = value
            delta = max(delta, abs(value - values[state]))
        values = updated
        if delta <= tolerance:
            break
    return values


@dataclass(frozen=True, slots=True)
class PolicyIterationResult:
    """A stationary policy and its state values."""

    policy: dict[str, str]
    values: dict[str, float]
    iterations: int


def policy_iteration(
    model: MdpModel,
    *,
    tolerance: float = 1e-9,
    max_iterations: int = 1000,
) -> PolicyIterationResult:
    """Solve a discounted infinite-horizon MDP with policy iteration."""
    if model.horizon is not None:
        raise ValueError("policy iteration needs an infinite horizon")
    policy: dict[str, str] = {}
    for state in model.states:
        actions = model.actions_for(state)
        if actions:
            policy[state] = actions[0]
    values = {state: 0.0 for state in model.states}

    for iteration in range(1, max_iterations + 1):
        for _ in range(max_iterations):
            updated: dict[str, float] = {}
            delta = 0.0
            for state in model.states:
                action = policy.get(state)
                value = (
                    0.0
                    if action is None
                    else _q_value(model, state, action, values)
                )
                updated[state] = value
                delta = max(delta, abs(value - values[state]))
            values = updated
            if delta <= tolerance:
                break

        changed = False
        for state in model.states:
            actions = model.actions_for(state)
            if not actions:
                continue
            best = max(
                actions,
                key=lambda action: _q_value(model, state, action, values),
            )
            if policy.get(state) != best:
                policy[state] = best
                changed = True
        if not changed:
            return PolicyIterationResult(
                policy=dict(policy),
                values=dict(values),
                iterations=iteration,
            )

    return PolicyIterationResult(
        policy=dict(policy),
        values=dict(values),
        iterations=max_iterations,
    )


def _lookahead_values(model: MdpModel) -> dict[str, float]:
    """Values of the states reached after the first action."""
    if model.horizon is None:
        return value_iteration(model)
    return value_iteration(model, horizon=max(-1, model.horizon - 1))


def action_values(
    model: MdpModel,
    state: str,
    *,
    values: dict[str, float] | None = None,
) -> tuple[tuple[str, float], ...]:
    """Return ``(action, expected value)`` in descending value order."""
    resolved = values if values is not None else _lookahead_values(model)
    rows = [
        (action, round(_q_value(model, state, action, resolved), 6))
        for action in model.actions_for(state)
    ]
    return tuple(sorted(rows, key=lambda item: (-item[1], item[0])))


class MDPPlanner:
    """Choose the action with the highest value in a finite MDP."""

    name = "mdp.v1"

    def __init__(self, model: MdpModel, *, state: str | None = None) -> None:
        self.model = model
        self.state = state or model.start
        self.version = self.name

    def solve(self, problem: PlannerInput) -> PlannerResult:
        state = str(problem.attributes.get("state", self.state))
        if state not in self.model.states:
            raise ValueError(f"unknown state: {state!r}")
        rows = action_values(self.model, state)
        if not rows:
            return PlannerResult(
                verb="wait",
                confidence=1.0,
                reason_code="terminal_state",
                rationale=f"{state} has no action to take",
                score=0.0,
                attributes={"state": state},
            )

        best_action, best_value = rows[0]
        second = rows[1][1] if len(rows) > 1 else None
        alternatives = tuple(
            {
                "action_id": action,
                "value": value,
                "rejected_because": "lower expected value",
            }
            for action, value in rows[1:]
        )
        return PlannerResult(
            verb="act",
            confidence=self._confidence(best_value, second),
            reason_code="mdp_plan",
            rationale=(
                f"{best_action} has the highest expected value "
                f"{best_value:.3f} from {state}"
            ),
            action_id=best_action,
            score=best_value,
            alternatives=alternatives,
            attributes={
                "state": state,
                "expected_value": best_value,
                "discount": self.model.discount,
                "horizon": self.model.horizon,
            },
        )

    @staticmethod
    def _confidence(best: float, second: float | None) -> float:
        if second is None:
            return 1.0
        gap = max(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / max(abs(best), 1e-9)))


def plan_actions(
    model: MdpModel,
    state: str | None = None,
) -> tuple[str, ...]:
    """Return the greedy action sequence for one state."""
    current = state or model.start
    path: list[str] = []
    seen: set[str] = set()
    while current not in seen:
        seen.add(current)
        rows = action_values(model, current)
        if not rows:
            break
        action = rows[0][0]
        path.append(f"{current}:{action}")
        outcomes = model.outgoing(current, action)
        if not outcomes:
            break
        current = sorted(
            outcomes,
            key=lambda item: (-item.probability, item.next_state),
        )[0].next_state
    return tuple(path)


__all__ = [
    "MDPPlanner",
    "MdpModel",
    "MdpTransition",
    "PolicyIterationResult",
    "action_values",
    "plan_actions",
    "policy_iteration",
    "value_iteration",
]
