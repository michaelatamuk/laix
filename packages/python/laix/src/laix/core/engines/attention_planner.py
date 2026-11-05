"""Attention-aware planning: human attention is a scarce resource.

The planner keeps the ordinary utility score and charges for the attention an
option needs: interruption, approval and escalation. A budget supplied by the
host limits how much attention the task may spend, so the planner can prefer a
direct action or wait instead of interrupting a person again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..decisions import ActionOption
from ..support.values import clamp
from .engine import DecisionProblem, Plan
from .utility import (
    UtilityEngine,
    UtilityModel,
    _approval_required,
    _constraint_blocker,
)

@dataclass(frozen=True, slots=True)
class AttentionWeights:
    """How much each kind of human attention costs."""

    interrupt: float = 0.4
    approval: float = 0.25
    escalation: float = 0.3
    exhausted: float = 1.0

    def __post_init__(self) -> None:
        for name in ("interrupt", "approval", "escalation", "exhausted"):
            if getattr(self, name) < 0:
                raise ValueError(f"attention weight {name!r} must not be negative")


@dataclass(frozen=True, slots=True)
class AttentionEffect:
    """The human-attention cost of one option."""

    interrupt_cost: float = 0.0
    requires_approval: bool = False
    escalates: bool = False
    interactive: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "interrupt_cost", clamp(self.interrupt_cost))

    @property
    def cost(self) -> float:
        """A comparable attention cost: interruption, approval, escalation and contact."""
        return (
            self.interrupt_cost
            + (0.5 if self.requires_approval else 0.0)
            + (0.5 if self.escalates else 0.0)
            + (0.5 if self.interactive else 0.0)
        )

    @property
    def requires_attention(self) -> bool:
        return self.cost > 0.0 or self.requires_approval or self.escalates


@dataclass(frozen=True, slots=True)
class AttentionScore:
    """The utility and attention parts of one option's score."""

    utility: float
    attention: float
    total: float
    effect: AttentionEffect
    remaining: float
    blocked: str | None = None


def attention_effect(option: ActionOption, *, approval: bool = False) -> AttentionEffect:
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
    )


def _remaining(problem: DecisionProblem) -> float:
    attributes = problem.attributes or {}
    budget = attributes.get("attention_budget", 1.0)
    spent = attributes.get("attention_spent", 0.0)
    try:
        budget_value = float(budget)
    except (TypeError, ValueError):
        budget_value = 1.0
    try:
        spent_value = float(spent)
    except (TypeError, ValueError):
        spent_value = 0.0
    try:
        remaining_value = float(
            attributes.get("attention_remaining", budget_value - spent_value)
        )
    except (TypeError, ValueError):
        remaining_value = budget_value - spent_value
    return max(0.0, remaining_value)


def _score_option(
    option: ActionOption,
    model: UtilityModel,
    weights: AttentionWeights,
    remaining: float,
    approval: bool,
) -> AttentionScore:
    effect = attention_effect(option, approval=approval)
    blocked = (
        "attention budget exhausted"
        if effect.requires_attention and effect.cost > remaining
        else None
    )
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


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: AttentionScore
    feasible: bool
    blocker: str | None


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
            score = _score_option(option, model, self.weights, remaining, approval)
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
            requires_approval=(
                best.option.requires_approval
                or best.option.destructive
                or approval
            ),
            reversible=best.option.reversible,
            score=best.score.total,
            alternatives=self._alternatives(rows, best.option.id),
            attributes={
                "utility": best.score.utility,
                "attention_score": best.score.attention,
                "attention_cost": best.score.effect.cost,
                "attention_remaining": best.score.remaining,
                "attention_budget_blocked": best.score.blocked,
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
    "AttentionEffect",
    "AttentionScore",
    "AttentionWeights",
    "attention_effect",
]
