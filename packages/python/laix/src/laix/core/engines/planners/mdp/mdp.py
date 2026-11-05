"""A small finite MDP planner with value iteration.

The app supplies the states, actions, transitions and rewards. The engine
returns the best action for one state, with the expected value and the
alternatives, so the result is explainable.
"""

from __future__ import annotations

from ....support.values import clamp
from ...contract.engine import DecisionProblem, Plan
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


class MDPEngine:
    """Choose the action with the highest value in a finite MDP."""

    name = "mdp.v1"

    def __init__(self, model: MdpModel, *, state: str | None = None) -> None:
        self.model = model
        self.state = state or model.start
        self.version = self.name

    def solve(self, problem: DecisionProblem) -> Plan:
        state = str(problem.attributes.get("state", self.state))
        if state not in self.model.states:
            raise ValueError(f"unknown state: {state!r}")
        rows = action_values(self.model, state)
        if not rows:
            return Plan(
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
        return Plan(
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
    "MDPEngine",
    "MdpModel",
    "MdpTransition",
    "action_values",
    "plan_actions",
    "value_iteration",
]
