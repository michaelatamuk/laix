"""The live composite planner.

The composite planner composes the four live planner scores into one decision: utility,
commitments, execution risk and human attention. It adds each term, so a single
plan can keep a promise, avoid an irreversible action and respect an attention
budget at the same time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ...support.time import parse_iso
from ...support.values import clamp
from ..planners.human_attention.human_attention_planner import (
    HumanAttentionWeights,
    _remaining,
    _score_option as human_attention_score,
    approval_state,
)
from ..planners.commitment.commitment_planner import (
    CommitmentWeights,
    _commitments,
    _score_option as commitment_score,
)
from ._live_row import _Row
from ..contract.planner_policy import PlannerInput, PlannerResult
from .composite_score import CompositeScore
from ..planners.execution.execution_planner import (
    ExecutionWeights,
    _receipt_status,
    _score_option as execution_score,
)
from ..planners.utility.utility_planner import (
    UtilityPlanner,
    UtilityModel,
    _approval_required,
    _constraint_blocker,
)


class LiveCompositePlanner:
    """Choose the option with the best combined live score."""

    name = "live.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        *,
        commitment_weights: CommitmentWeights | None = None,
        execution_weights: ExecutionWeights | None = None,
        human_attention_weights: HumanAttentionWeights | None = None,
        enforce_feasibility: bool = True,
    ) -> None:
        self.model = model
        self.commitment_weights = commitment_weights or CommitmentWeights()
        self.execution_weights = execution_weights or ExecutionWeights()
        self.human_attention_weights = human_attention_weights or HumanAttentionWeights()
        self.enforce_feasibility = enforce_feasibility
        self._utility = UtilityPlanner(model)

    def solve(self, problem: PlannerInput) -> PlannerResult:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        commitments = _commitments(problem)
        now = parse_iso(problem.at) or datetime.now(timezone.utc)
        approval = _approval_required(problem)
        remaining = _remaining(problem)
        rows: list[_Row] = []
        for option in options:
            commitment = commitment_score(
                option,
                model,
                commitments,
                self.commitment_weights,
                now,
            )
            execution = execution_score(
                option,
                model,
                self.execution_weights,
                approval,
                _receipt_status(problem, option),
            )
            attention = human_attention_score(
                option,
                model,
                self.human_attention_weights,
                remaining,
                approval,
                approval_state(problem, option),
            )
            blocker = _constraint_blocker(problem, option)
            score = CompositeScore(
                utility=commitment.utility,
                commitment=commitment.commitment,
                execution=execution.execution,
                human_attention=attention.human_attention,
                total=round(
                    commitment.utility
                    + commitment.commitment
                    + execution.execution
                    + attention.human_attention,
                    6,
                ),
            )
            blocked = commitment.blocked or attention.blocked or blocker
            rows.append(
                _Row(
                    option=option,
                    score=score,
                    feasible=(
                        model.feasible(option) and blocked is None
                        if self.enforce_feasibility
                        else True
                    ),
                    blocker=blocked,
                    commitment=commitment,
                    execution=execution,
                    human_attention=attention,
                )
            )

        feasible = [row for row in rows if row.feasible]
        if not feasible:
            return self._wait(
                "no_feasible_option",
                "every option breaks a hard limit or an attention constraint",
            )

        feasible.sort(key=lambda row: (-row.score.total, row.option.id))
        best = feasible[0]
        second = feasible[1].score.total if len(feasible) > 1 else None
        return PlannerResult(
            verb=best.option.verb,
            confidence=self._confidence(best.score.total, second),
            reason_code="live_decision",
            rationale=(
                f"{best.option.id} balances utility {best.score.utility:.3f}, "
                f"commitments {best.score.commitment:+.3f}, "
                f"execution {best.score.execution:+.3f} and "
                f"attention {best.score.human_attention:+.3f}"
            ),
            action_id=best.option.id,
            requires_approval=(
                best.human_attention.effect.requires_approval
                or best.execution.requires_approval
            ),
            reversible=best.option.reversible,
            score=best.score.total,
            alternatives=self._alternatives(rows, best.option.id),
            attributes={
                "utility": best.score.utility,
                "commitment_score": best.score.commitment,
                "execution_score": best.score.execution,
                "human_attention_score": best.score.human_attention,
                "human_attention_cost": best.human_attention.effect.cost,
                "commitments_fulfilled": list(best.commitment.fulfilled),
                "commitments_violated": list(best.commitment.violated),
                "commitments_created": list(best.commitment.created),
                "receipt_status": best.execution.receipt_status,
                "approval_state": best.human_attention.effect.approval_state,
            },
        )

    @staticmethod
    def _alternatives(rows: list[_Row], best_id: str) -> tuple[dict[str, Any], ...]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            if row.option.id == best_id:
                continue
            if row.blocker:
                reason = f"blocked by {row.blocker}"
            elif not row.feasible:
                reason = "outside the hard limits"
            else:
                reason = "lower integrated score"
            payload.append(
                {
                    "action_id": row.option.id,
                    "verb": row.option.verb,
                    "name": row.option.name,
                    "utility": row.score.utility,
                    "commitment": row.score.commitment,
                    "execution": row.score.execution,
                    "human_attention": row.score.human_attention,
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


__all__ = ["LiveCompositePlanner", "CompositeScore"]
