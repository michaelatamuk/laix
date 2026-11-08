"""Commitment-attention branch and bound (CABB).

CABB is an exact planner for a finite, deterministic sequence of LAIX
decisions. It chooses one option per step under open commitments and a shared
human-attention budget. The search is exact for the supplied finite scenario.

The candidate contribution is the problem formulation and the two admissible
bounds: a relaxed per-step score and a terminal promise bound. Prior-art review
is still required before calling it a new algorithmic primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from ...commitments import Commitment
from ...decisions import ActionOption
from ...support.time import parse_iso
from ..planners.commitment.commitment_planner import (
    CommitmentWeights,
    _score_option as commitment_score,
)
from ..planners.execution.execution_planner import (
    ExecutionWeights,
    _score_option as execution_score,
)
from ..planners.human_attention.human_attention_planner import (
    HumanAttentionWeights,
    _score_option as human_attention_score,
)
from ..planners.utility.utility_planner import UtilityModel
from .contract import DecisionPlan, DecisionScenario, DecisionStep


@dataclass(frozen=True, slots=True)
class _Scored:
    option: ActionOption
    immediate: float
    remaining: float
    fulfilled: tuple[str, ...]
    violated: tuple[str, ...]
    blocked: bool


class CABBPlanner:
    """Exact branch-and-bound planning for a finite decision sequence."""

    name = "cabb.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        *,
        commitment_weights: CommitmentWeights | None = None,
        execution_weights: ExecutionWeights | None = None,
        human_attention_weights: HumanAttentionWeights | None = None,
    ) -> None:
        self.model = model or UtilityModel()
        self.commitment_weights = commitment_weights or CommitmentWeights()
        self.execution_weights = execution_weights or ExecutionWeights()
        self.human_attention_weights = human_attention_weights or HumanAttentionWeights()

    def plan(self, scenario: DecisionScenario) -> DecisionPlan:
        if not scenario.steps:
            return DecisionPlan((), 0.0, 0.0, (), 0, True)
        statuses = {item.id: item.status for item in scenario.commitments}
        initial_attention = self._initial_attention(scenario)
        final_at = parse_iso(scenario.steps[-1].at) or datetime.now(timezone.utc)
        commitment_ceiling = sum(
            self.commitment_weights.keep * (0.5 + item.priority)
            + self.commitment_weights.due * (0.5 + item.priority)
            for item in scenario.commitments
        )
        bounds = [self._relaxed_bound(step, commitment_ceiling) for step in scenario.steps]
        best: dict[str, Any] = {
            "score": float("-inf"),
            "actions": (),
            "remaining": initial_attention,
            "violations": (),
        }
        nodes = 0

        def search(
            index: int,
            current: dict[str, str],
            remaining: float,
            score: float,
            actions: tuple[str, ...],
            violations: tuple[str, ...],
        ) -> None:
            nonlocal nodes
            nodes += 1
            if index == len(scenario.steps):
                total = score - self._terminal_penalty(scenario, current, final_at)
                if total > best["score"]:
                    best.update(
                        score=total,
                        actions=actions,
                        remaining=remaining,
                        violations=violations,
                    )
                return
            if score + sum(bounds[index:]) <= best["score"]:
                return
            step = scenario.steps[index]
            now = parse_iso(step.at) or datetime.now(timezone.utc)
            for option in step.options:
                scored = self._score(scenario, option, current, remaining, now)
                if scored.blocked:
                    continue
                search(
                    index + 1,
                    self._apply(current, scored),
                    scored.remaining,
                    score + scored.immediate,
                    actions + (option.id,),
                    violations + scored.violated,
                )

        search(0, statuses, initial_attention, 0.0, (), ())
        if best["score"] == float("-inf"):
            return DecisionPlan((), 0.0, 0.0, (), nodes, True)
        spent = (
            initial_attention - best["remaining"]
            if initial_attention != float("inf")
            else 0.0
        )
        return DecisionPlan(
            actions=tuple(best["actions"]),
            score=round(best["score"], 6),
            attention_spent=round(spent, 6),
            violations=tuple(best["violations"]),
            nodes=nodes,
            optimal=True,
        )

    def evaluate(self, scenario: DecisionScenario, actions: tuple[str, ...]) -> DecisionPlan:
        """Replay a fixed action sequence with the CABB score."""
        if len(actions) != len(scenario.steps):
            raise ValueError("actions must match the number of steps")
        if not scenario.steps:
            return DecisionPlan((), 0.0, 0.0, (), 0, False)
        statuses = {item.id: item.status for item in scenario.commitments}
        initial_attention = self._initial_attention(scenario)
        remaining = initial_attention
        score = 0.0
        violations: list[str] = []
        final_at = parse_iso(scenario.steps[-1].at) or datetime.now(timezone.utc)
        for step, action_id in zip(scenario.steps, actions):
            option = next((item for item in step.options if item.id == action_id), None)
            if option is None:
                raise ValueError(f"unknown action {action_id!r} at {step.at}")
            now = parse_iso(step.at) or datetime.now(timezone.utc)
            scored = self._score(scenario, option, statuses, remaining, now)
            if scored.blocked:
                raise ValueError(f"action {action_id!r} is blocked at {step.at}")
            score += scored.immediate
            statuses = self._apply(statuses, scored)
            violations.extend(scored.violated)
            remaining = scored.remaining
        penalty = self._terminal_penalty(scenario, statuses, final_at)
        spent = (
            initial_attention - remaining
            if initial_attention != float("inf")
            else 0.0
        )
        return DecisionPlan(
            actions=actions,
            score=round(score - penalty, 6),
            attention_spent=round(spent, 6),
            violations=tuple(violations),
            nodes=0,
            optimal=False,
        )

    def greedy_actions(
        self,
        scenario: DecisionScenario,
        prefix: tuple[str, ...] = (),
    ) -> tuple[str, ...]:
        """Complete a scenario by taking the best immediate option at each step."""
        if len(prefix) > len(scenario.steps):
            raise ValueError("the prefix is longer than the scenario")
        statuses = {item.id: item.status for item in scenario.commitments}
        remaining = self._initial_attention(scenario)
        actions = list(prefix)
        for step, action_id in zip(scenario.steps, prefix):
            option = next((item for item in step.options if item.id == action_id), None)
            if option is None:
                raise ValueError(f"unknown action {action_id!r} at {step.at}")
            now = parse_iso(step.at) or datetime.now(timezone.utc)
            scored = self._score(scenario, option, statuses, remaining, now)
            statuses = self._apply(statuses, scored)
            remaining = scored.remaining
        for step in scenario.steps[len(prefix):]:
            now = parse_iso(step.at) or datetime.now(timezone.utc)
            best: _Scored | None = None
            for option in step.options:
                scored = self._score(scenario, option, statuses, remaining, now)
                if scored.blocked:
                    continue
                if (
                    best is None
                    or scored.immediate > best.immediate
                    or (
                        scored.immediate == best.immediate
                        and option.id < best.option.id
                    )
                ):
                    best = scored
            if best is None:
                break
            actions.append(best.option.id)
            statuses = self._apply(statuses, best)
            remaining = best.remaining
        return tuple(actions)

    def advance(
        self,
        scenario: DecisionScenario,
        actions: tuple[str, ...],
    ) -> tuple[tuple[Commitment, ...], float]:
        """Return commitments and remaining attention after a fixed prefix."""
        if len(actions) > len(scenario.steps):
            raise ValueError("the prefix is longer than the scenario")
        statuses = {item.id: item.status for item in scenario.commitments}
        remaining = self._initial_attention(scenario)
        for step, action_id in zip(scenario.steps, actions):
            option = next((item for item in step.options if item.id == action_id), None)
            if option is None:
                raise ValueError(f"unknown action {action_id!r} at {step.at}")
            now = parse_iso(step.at) or datetime.now(timezone.utc)
            scored = self._score(scenario, option, statuses, remaining, now)
            statuses = self._apply(statuses, scored)
            remaining = scored.remaining
        commitments = tuple(
            replace(item, status=statuses[item.id]) for item in scenario.commitments
        )
        return commitments, remaining

    def _score(
        self,
        scenario: DecisionScenario,
        option: ActionOption,
        statuses: dict[str, str],
        remaining: float,
        now: datetime,
    ) -> _Scored:
        commitments = {
            item.id: replace(item, status=statuses[item.id])
            for item in scenario.commitments
        }
        commitment = commitment_score(
            option,
            self.model,
            commitments,
            self.commitment_weights,
            now,
        )
        execution = execution_score(
            option,
            self.model,
            self.execution_weights,
            False,
            None,
        )
        attention = human_attention_score(
            option,
            self.model,
            self.human_attention_weights,
            remaining,
            False,
            None,
        )
        return _Scored(
            option=option,
            immediate=(
                commitment.utility
                + commitment.commitment
                + execution.execution
                + attention.human_attention
            ),
            remaining=attention.remaining,
            fulfilled=tuple(commitment.fulfilled),
            violated=tuple(commitment.violated),
            blocked=bool(commitment.blocked or attention.blocked),
        )

    @staticmethod
    def _apply(statuses: dict[str, str], scored: _Scored) -> dict[str, str]:
        updated = dict(statuses)
        for commitment_id in scored.fulfilled:
            updated[commitment_id] = "done"
        for commitment_id in scored.violated:
            updated[commitment_id] = "cancelled"
        return updated

    @staticmethod
    def _initial_attention(scenario: DecisionScenario) -> float:
        if scenario.human_attention_budget is None:
            return float("inf")
        return scenario.human_attention_budget.remaining()

    @staticmethod
    def _terminal_penalty(
        scenario: DecisionScenario,
        statuses: dict[str, str],
        final_at: datetime,
    ) -> float:
        commitments = {item.id: item for item in scenario.commitments}
        penalty = 0.0
        for commitment_id, status in statuses.items():
            if status != "open":
                continue
            item = commitments.get(commitment_id)
            if item is None:
                continue
            due = parse_iso(item.due) if item.due else None
            if due is None or due <= final_at:
                penalty += scenario.open_penalty * (0.5 + item.priority)
        return penalty

    def _relaxed_bound(self, step: DecisionStep, commitment_ceiling: float) -> float:
        if not step.options:
            return 0.0
        return max(self.model.score(option) for option in step.options) + commitment_ceiling


def plan_decisions(scenario: DecisionScenario, **kwargs: Any) -> DecisionPlan:
    """Functional shortcut for one CABB plan."""
    return CABBPlanner(**kwargs).plan(scenario)


__all__ = ["CABBPlanner", "plan_decisions"]
