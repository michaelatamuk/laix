"""Commitment-attention value of decision (CA-VOD).

This is a deterministic one-step lookahead over the five decision verbs. It
starts from the live composite score and adds an explicit information value for
``ask``, ``verify`` and ``observe`` and an option value for ``wait``.

The full CA-VOD formulation is a constrained POMDP. This module is the
low-latency prototype: it uses the host's uncertainty and the option's declared
information gain instead of solving a belief-state MDP.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ....decisions import ActionOption
from ....support.time import parse_iso
from ....support.values import clamp
from ...contract.planner_policy import PlannerInput, PlannerResult
from ..commitment.commitment_planner import (
    CommitmentWeights,
    _commitments,
    _score_option as commitment_score,
)
from ..execution.execution_planner import (
    ExecutionWeights,
    _receipt_status,
    _score_option as execution_score,
)
from ..human_attention.human_attention_planner import (
    HumanAttentionWeights,
    _remaining,
    _score_option as human_attention_score,
    approval_state,
)
from ..utility.utility_planner import (
    UtilityModel,
    UtilityPlanner,
    _approval_required,
    _constraint_blocker,
)


_INFORMATION_GAIN = {
    "ask": 0.7,
    "verify": 0.5,
    "observe": 0.4,
}


@dataclass(frozen=True, slots=True)
class CAVODWeights:
    """Weights for the one-step value-of-decision terms."""

    information: float = 0.5
    waiting: float = 0.25
    uncertainty: float = 0.5


@dataclass(frozen=True, slots=True)
class CAVODScore:
    """The four live terms plus the information and option values."""

    utility: float
    commitment: float
    execution: float
    human_attention: float
    information: float
    option: float
    total: float


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: CAVODScore
    feasible: bool
    blocker: str | None
    commitment: Any = field(repr=False)
    execution: Any = field(repr=False)
    human_attention: Any = field(repr=False)


def _decision_value(option: ActionOption) -> Mapping[str, Any]:
    params = getattr(option, "params", {}) or {}
    payload = params.get("decision_value", params.get("value", {}))
    return payload if isinstance(payload, Mapping) else {}


def _uncertainty(problem: PlannerInput, weights: CAVODWeights) -> float:
    raw = (problem.attributes or {}).get("uncertainty")
    if raw is not None:
        try:
            return clamp(float(raw))
        except (TypeError, ValueError):
            pass
    if problem.situation is not None:
        try:
            return clamp(1.0 - problem.situation.confidence())
        except AttributeError:
            pass
    return clamp(weights.uncertainty)


def _information_value(
    option: ActionOption,
    uncertainty: float,
    weights: CAVODWeights,
) -> float:
    payload = _decision_value(option)
    explicit = payload.get("information_value")
    if explicit is not None:
        try:
            return round(max(0.0, float(explicit)), 6)
        except (TypeError, ValueError):
            pass
    gain = payload.get("information_gain", _INFORMATION_GAIN.get(option.verb, 0.0))
    try:
        gain_value = max(0.0, float(gain))
    except (TypeError, ValueError):
        gain_value = 0.0
    return round(weights.information * uncertainty * gain_value, 6)


def _option_value(
    option: ActionOption,
    uncertainty: float,
    weights: CAVODWeights,
) -> float:
    if option.verb != "wait":
        return 0.0
    payload = _decision_value(option)
    explicit = payload.get("option_value")
    if explicit is not None:
        try:
            return round(max(0.0, float(explicit)), 6)
        except (TypeError, ValueError):
            pass
    return round(weights.waiting * uncertainty, 6)


class CAVODPlanner:
    """Choose the option with the best one-step value of decision.

    The planner composes the same four live terms as ``LiveCompositePlanner``
    and adds:

    - ``information`` for verbs that reduce uncertainty;
    - ``option`` for ``wait``.

    It is deterministic and training-free. It does not need a model or a
    transition table.
    """

    name = "ca_vod.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        *,
        weights: CAVODWeights | None = None,
        commitment_weights: CommitmentWeights | None = None,
        execution_weights: ExecutionWeights | None = None,
        human_attention_weights: HumanAttentionWeights | None = None,
        enforce_feasibility: bool = True,
    ) -> None:
        self.model = model
        self.weights = weights or CAVODWeights()
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
        uncertainty = _uncertainty(problem, self.weights)
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
            information = _information_value(option, uncertainty, self.weights)
            option_value = _option_value(option, uncertainty, self.weights)
            blocker = _constraint_blocker(problem, option)
            total = round(
                commitment.utility
                + commitment.commitment
                + execution.execution
                + attention.human_attention
                + information
                + option_value,
                6,
            )
            score = CAVODScore(
                utility=commitment.utility,
                commitment=commitment.commitment,
                execution=execution.execution,
                human_attention=attention.human_attention,
                information=information,
                option=option_value,
                total=total,
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
            reason_code="value_of_decision",
            rationale=(
                f"{best.option.id} balances utility {best.score.utility:.3f}, "
                f"commitment {best.score.commitment:+.3f}, "
                f"execution {best.score.execution:+.3f}, "
                f"attention {best.score.human_attention:+.3f}, "
                f"information {best.score.information:+.3f} and "
                f"option value {best.score.option:+.3f}"
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
                "algorithm": self.name,
                "utility": best.score.utility,
                "commitment_score": best.score.commitment,
                "execution_score": best.score.execution,
                "human_attention_score": best.score.human_attention,
                "information_value": best.score.information,
                "option_value": best.score.option,
                "uncertainty": uncertainty,
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
                reason = "lower value of decision"
            payload.append(
                {
                    "action_id": row.option.id,
                    "verb": row.option.verb,
                    "name": row.option.name,
                    "utility": row.score.utility,
                    "commitment": row.score.commitment,
                    "execution": row.score.execution,
                    "human_attention": row.score.human_attention,
                    "information": row.score.information,
                    "option": row.score.option,
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
    "CAVODPlanner",
    "CAVODScore",
    "CAVODWeights",
]
