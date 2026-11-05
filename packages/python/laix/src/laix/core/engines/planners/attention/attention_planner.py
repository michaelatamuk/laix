"""Attention-aware planning: human attention is a scarce resource.

The planner keeps the ordinary utility score and charges for the attention an
option needs: interruption, approval and escalation. A budget supplied by the
host limits how much attention the task may spend, so the planner can prefer a
direct action or wait instead of interrupting a person again.
"""

from __future__ import annotations

from typing import Any

from ....decisions import ActionOption
from ....support.values import clamp
from ._attention_row import _Row
from .attention_budget import AttentionBudget
from .attention_effect import AttentionEffect
from .attention_score import AttentionScore
from .attention_weights import AttentionWeights
from ...engine import DecisionProblem, Plan
from ..utility.utility import (
    UtilityEngine,
    UtilityModel,
    _approval_required,
    _constraint_blocker,
)


def attention_effect(
    option: ActionOption,
    *,
    approval: bool = False,
    approval_state: str | None = None,
) -> AttentionEffect:
    """Read an option's human-attention cost from its fields and ``params``."""
    params = getattr(option, "params", {}) or {}
    payload = params.get("attention", params)
    if not isinstance(payload, dict):
        payload = params
    interrupt = payload.get("interrupt_cost", option.interrupt_cost)
    requires_approval = bool(
        approval
        or payload.get("requires_approval", option.requires_approval or option.destructive)
    )
    if approval_state == "approved":
        requires_approval = False
    elif approval_state in {"pending", "rejected"}:
        requires_approval = True
    escalates = bool(payload.get("escalates", option.verb == "escalate"))
    try:
        interrupt_value = float(interrupt)
    except (TypeError, ValueError):
        interrupt_value = option.interrupt_cost
    return AttentionEffect(
        interrupt_cost=interrupt_value,
        requires_approval=requires_approval,
        escalates=escalates,
        interactive=option.verb in {"ask", "guide"},
        approval_state=approval_state,
    )


def approval_state(problem: DecisionProblem, option: ActionOption) -> str | None:
    """Read the host's approval state for one option, if it supplied one."""
    raw = (problem.attributes or {}).get("approvals")
    if isinstance(raw, dict):
        value = raw.get(option.id, raw.get(option.name))
        if value is None:
            return None
        if isinstance(value, bool):
            return "approved" if value else "rejected"
        return str(value)
    if isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("action_id", item.get("action_name"))
                status = item.get("status")
                if status is None and "approved" in item:
                    status = "approved" if item["approved"] else "rejected"
            else:
                name = getattr(item, "action_name", None)
                status = getattr(item, "status", None)
                if status is None and hasattr(item, "approved"):
                    status = "approved" if getattr(item, "approved") else "rejected"
            if name in {option.id, option.name} and status is not None:
                return str(status)
    return None


def _remaining(problem: DecisionProblem) -> float:
    attributes = problem.attributes or {}
    raw = attributes.get("attention_budget", 1.0)
    if isinstance(raw, AttentionBudget):
        base = raw.remaining()
    elif isinstance(raw, dict):
        base = float(raw.get("total", 1.0)) - float(raw.get("spent", 0.0))
    else:
        try:
            base = float(raw)
        except (TypeError, ValueError):
            base = 1.0
        spent = attributes.get("attention_spent", 0.0)
        try:
            base -= float(spent)
        except (TypeError, ValueError):
            pass
    try:
        remaining_value = float(attributes.get("attention_remaining", base))
    except (TypeError, ValueError):
        remaining_value = base
    return max(0.0, remaining_value)


def _score_option(
    option: ActionOption,
    model: UtilityModel,
    weights: AttentionWeights,
    remaining: float,
    approval: bool,
    state: str | None,
) -> AttentionScore:
    effect = attention_effect(option, approval=approval, approval_state=state)
    if state == "rejected":
        blocked = "approval rejected"
    elif effect.requires_attention and effect.cost > remaining:
        blocked = "attention budget exhausted"
    else:
        blocked = None
    attention = (
        -weights.interrupt * effect.interrupt_cost
        - weights.approval * (1.0 if effect.requires_approval else 0.0)
        - weights.escalation * (1.0 if effect.escalates else 0.0)
        - weights.exhausted * (1.0 if blocked else 0.0)
    )
    utility = model.score(option)
    return AttentionScore(
        utility=round(utility, 6),
        attention=round(attention, 6),
        total=round(utility + attention, 6),
        effect=effect,
        remaining=max(0.0, remaining - effect.cost),
        blocked=blocked,
    )


class AttentionAwareEngine:
    """Choose the option with the best utility plus human-attention cost."""

    name = "attention.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        weights: AttentionWeights | None = None,
    ) -> None:
        self.model = model
        self.weights = weights or AttentionWeights()
        self._utility = UtilityEngine(model)

    def solve(self, problem: DecisionProblem) -> Plan:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        remaining = _remaining(problem)
        approval = _approval_required(problem)
        rows: list[_Row] = []
        for option in options:
            state = approval_state(problem, option)
            score = _score_option(
                option,
                model,
                self.weights,
                remaining,
                approval,
                state,
            )
            blocker = _constraint_blocker(problem, option)
            rows.append(
                _Row(
                    option=option,
                    score=score,
                    feasible=model.feasible(option)
                    and blocker is None
                    and score.blocked is None,
                    blocker=score.blocked or blocker,
                )
            )

        feasible = [row for row in rows if row.feasible]
        if not feasible:
            if any(row.blocker == "approval rejected" for row in rows):
                return self._wait(
                    "approval_rejected",
                    "every remaining option was rejected or needs more attention",
                )
            return self._wait(
                "attention_budget_exhausted",
                "every option needs more human attention than is left",
            )

        feasible.sort(key=lambda row: (-row.score.total, row.option.id))
        best = feasible[0]
        second = feasible[1].score.total if len(feasible) > 1 else None
        return Plan(
            verb=best.option.verb,
            confidence=self._confidence(best.score.total, second),
            reason_code="attention_aware",
            rationale=(
                f"{best.option.id} balances utility {best.score.utility:.3f} "
                f"and attention cost {best.score.attention:+.3f}"
            ),
            action_id=best.option.id,
            requires_approval=best.score.effect.requires_approval,
            reversible=best.option.reversible,
            score=best.score.total,
            alternatives=self._alternatives(rows, best.option.id),
            attributes={
                "utility": best.score.utility,
                "attention_score": best.score.attention,
                "attention_cost": best.score.effect.cost,
                "attention_remaining": best.score.remaining,
                "attention_budget_blocked": best.score.blocked,
                "approval_state": best.score.effect.approval_state,
            },
        )

    @staticmethod
    def _alternatives(rows: list[_Row], best_id: str) -> tuple[dict[str, Any], ...]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            if row.option.id == best_id:
                continue
            reason = (
                f"blocked by {row.blocker}"
                if row.blocker
                else (
                    "outside the hard limits"
                    if not row.feasible
                    else "lower attention-adjusted score"
                )
            )
            payload.append(
                {
                    "action_id": row.option.id,
                    "verb": row.option.verb,
                    "name": row.option.name,
                    "utility": row.score.utility,
                    "attention": row.score.attention,
                    "total": row.score.total,
                    "rejected_because": reason,
                }
            )
        payload.sort(key=lambda item: (-float(item["total"]), str(item["action_id"])))
        return tuple(payload)

    @staticmethod
    def _confidence(best: float, second: float | None) -> float:
        if second is None:
            return 1.0
        gap = max(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / max(abs(best), 1e-9)))

    @staticmethod
    def _wait(reason_code: str, rationale: str) -> Plan:
        return Plan(
            verb="wait",
            confidence=1.0,
            reason_code=reason_code,
            rationale=rationale,
            score=0.0,
        )


__all__ = [
    "AttentionAwareEngine",
    "AttentionBudget",
    "AttentionEffect",
    "AttentionScore",
    "AttentionWeights",
    "approval_state",
    "attention_effect",
]
