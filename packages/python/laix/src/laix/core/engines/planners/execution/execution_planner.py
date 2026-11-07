"""Execution-aware planning: the cost of acting is part of the decision.

The planner keeps the ordinary utility score and adds execution risk: an
action may be irreversible, may have an unknown outcome, may need approval and
may cost time or money to recover from. It is deterministic and training-free;
the execution facts come from the option and from the host's constraints.
"""

from __future__ import annotations

from typing import Any

from ....decisions import ActionOption
from ....support.values import clamp
from ._execution_row import _Row
from ...contract.planner_policy import PlannerInput, PlannerResult
from .execution_effect import ExecutionEffect
from .execution_score import ExecutionScore
from .execution_weights import ExecutionWeights
from ..utility.utility_planner import (
    UtilityPlanner,
    UtilityModel,
    _approval_required,
    _constraint_blocker,
)


def execution_effect(option: ActionOption) -> ExecutionEffect:
    """Read an option's execution facts from ``params``.

    Supported shape::

        params={"execution": {"unknown_risk": 0.4, "recovery_cost": 0.2}}
        params={"unknown_risk": 0.4, "recovery_cost": 0.2}
    """
    params = getattr(option, "params", {}) or {}
    payload = params.get("execution", params)
    if not isinstance(payload, dict):
        return ExecutionEffect()
    unknown = payload.get("unknown_risk", params.get("unknown_risk", 0.0))
    recovery = payload.get("recovery_cost", params.get("recovery_cost", 0.0))
    try:
        unknown_value = float(unknown)
    except (TypeError, ValueError):
        unknown_value = 0.0
    try:
        recovery_value = float(recovery)
    except (TypeError, ValueError):
        recovery_value = 0.0
    return ExecutionEffect(
        unknown_risk=unknown_value,
        recovery_cost=recovery_value,
    )


def _receipt_status(problem: PlannerInput, option: ActionOption) -> str | None:
    attributes = problem.attributes or {}
    raw = attributes.get("execution_state")
    if isinstance(raw, dict):
        value = raw.get(option.id)
        return str(value) if value is not None else None
    receipts = attributes.get("execution_receipts")
    if not receipts:
        return None
    for receipt in receipts:
        if isinstance(receipt, dict):
            name = receipt.get("action_name")
            status = receipt.get("status")
        else:
            name = getattr(receipt, "action_name", None)
            status = getattr(receipt, "status", None)
        if name in {option.id, option.name} and status is not None:
            return str(status)
    return None


def _score_option(
    option: ActionOption,
    model: UtilityModel,
    weights: ExecutionWeights,
    approval: bool,
    receipt_status: str | None,
) -> ExecutionScore:
    effect = execution_effect(option)
    irreversible = not option.reversible
    requires_approval = (
        approval or option.requires_approval or option.destructive
    )
    unknown_risk = effect.unknown_risk
    recovery_cost = effect.recovery_cost
    if receipt_status == "unknown":
        unknown_risk = max(unknown_risk, 1.0)
    elif receipt_status in {"failed", "refused", "cancelled", "undone"}:
        recovery_cost = max(recovery_cost, 1.0)
    elif receipt_status == "pending":
        requires_approval = True
    execution = (
        -weights.irreversible * (1.0 if irreversible else 0.0)
        - weights.unknown * unknown_risk
        - weights.approval * (1.0 if requires_approval else 0.0)
        - weights.recovery * recovery_cost
    )
    utility = model.score(option)
    return ExecutionScore(
        utility=round(utility, 6),
        execution=round(execution, 6),
        total=round(utility + execution, 6),
        irreversible=irreversible,
        unknown_risk=unknown_risk,
        recovery_cost=recovery_cost,
        requires_approval=requires_approval,
        receipt_status=receipt_status,
    )


class ExecutionRiskPlanner:
    """Choose the option with the best utility plus execution risk."""

    name = "execution.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        weights: ExecutionWeights | None = None,
    ) -> None:
        self.model = model
        self.weights = weights or ExecutionWeights()
        self._utility = UtilityPlanner(model)

    def solve(self, problem: PlannerInput) -> PlannerResult:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        approval = _approval_required(problem)
        rows: list[_Row] = []
        for option in options:
            score = _score_option(
                option,
                model,
                self.weights,
                approval,
                _receipt_status(problem, option),
            )
            blocker = _constraint_blocker(problem, option)
            rows.append(
                _Row(
                    option=option,
                    score=score,
                    feasible=model.feasible(option) and blocker is None,
                    blocker=blocker,
                )
            )

        feasible = [row for row in rows if row.feasible]
        if not feasible:
            return self._wait(
                "no_feasible_option",
                "every option is outside the hard limits",
            )

        feasible.sort(key=lambda row: (-row.score.total, row.option.id))
        best = feasible[0]
        second = feasible[1].score.total if len(feasible) > 1 else None
        return PlannerResult(
            verb=best.option.verb,
            confidence=self._confidence(best.score.total, second),
            reason_code="execution_aware",
            rationale=(
                f"{best.option.id} balances utility {best.score.utility:.3f} "
                f"and execution cost {best.score.execution:+.3f}"
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
                "execution_score": best.score.execution,
                "irreversible": best.score.irreversible,
                "unknown_risk": best.score.unknown_risk,
                "recovery_cost": best.score.recovery_cost,
                "requires_approval": best.score.requires_approval,
                "receipt_status": best.score.receipt_status,
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
                    else "lower execution-adjusted score"
                )
            )
            payload.append(
                {
                    "action_id": row.option.id,
                    "verb": row.option.verb,
                    "name": row.option.name,
                    "utility": row.score.utility,
                    "execution": row.score.execution,
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
    def _wait(reason_code: str, rationale: str) -> PlannerResult:
        return PlannerResult(
            verb="wait",
            confidence=1.0,
            reason_code=reason_code,
            rationale=rationale,
            score=0.0,
        )


__all__ = [
    "ExecutionRiskPlanner",
    "ExecutionEffect",
    "ExecutionScore",
    "ExecutionWeights",
    "execution_effect",
]
