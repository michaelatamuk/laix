"""Commitment-attention value of decision (CA-VOD).

This is a deterministic one-step lookahead over the five decision verbs. It
starts from the live composite score and adds an explicit information value for
``ask``, ``verify`` and ``observe`` and an option value for ``wait``.

The full CA-VOD formulation is a constrained POMDP. This module uses the
host's uncertainty and the option's declared information gain for the one-step
terms. Pass ``pomdp_model=`` and ``belief=`` to add a finite-horizon
belief-state future value without double-counting the immediate reward.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from ....domain.decisions import ActionOption
from ....support.time import parse_iso
from ....support.values import clamp
from ....contract.planner_policy import PlannerInput, PlannerResult
from ..commitment.commitment_planner import (
    CommitmentWeights,
    _active_and_graph,
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
from ..pomdp.pomdp_model import PomdpModel
from ..pomdp.pomdp_planner import (
    action_future_value,
    belief_entropy,
    belief_from_state,
    normalize_belief,
)
from ..utility.utility_planner import (
    UtilityModel,
    UtilityPlanner,
    _approval_required,
    _constraint_blocker,
)
from ._ca_vod_row import _Row
from .ca_vod_score import CAVODScore
from .ca_vod_weights import CAVODWeights


_INFORMATION_GAIN = {
    "ask": 0.7,
    "verify": 0.5,
    "observe": 0.4,
}


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
    - ``option`` for ``wait``;
    - ``future`` when a ``PomdpModel`` and a belief are supplied.

    It is deterministic and training-free. The one-step path does not need a
    model; the future-value path only needs a small, host-supplied model.
    """

    name = "ca_vod.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        *,
        pomdp_model: PomdpModel | None = None,
        belief: Mapping[str, float] | None = None,
        weights: CAVODWeights | None = None,
        commitment_weights: CommitmentWeights | None = None,
        execution_weights: ExecutionWeights | None = None,
        human_attention_weights: HumanAttentionWeights | None = None,
        enforce_feasibility: bool = True,
        require_verified: bool = True,
        max_verification_age: timedelta | None = None,
    ) -> None:
        self.model = model
        self.pomdp_model = pomdp_model
        self.belief = dict(belief or {})
        self.weights = weights or CAVODWeights()
        self.commitment_weights = commitment_weights or CommitmentWeights()
        self.execution_weights = execution_weights or ExecutionWeights()
        self.human_attention_weights = human_attention_weights or HumanAttentionWeights()
        self.enforce_feasibility = enforce_feasibility
        self.require_verified = require_verified
        self.max_verification_age = max_verification_age
        self._utility = UtilityPlanner(model)

    def solve(self, problem: PlannerInput) -> PlannerResult:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        commitments, graph = _active_and_graph(problem)
        now = parse_iso(problem.at) or datetime.now(timezone.utc)

        def is_blocked(commitment_id: str) -> bool:
            commitment = commitments.get(commitment_id)
            return True if commitment is None else graph.blocked(
                commitment,
                require_verified=self.require_verified,
                now=now,
                max_verification_age=self.max_verification_age,
            )

        approval = _approval_required(problem)
        remaining = _remaining(problem)
        uncertainty = _uncertainty(problem, self.weights)
        belief = self._resolve_belief(problem) if self.pomdp_model else {}
        horizon = (
            int((problem.attributes or {}).get("horizon", self.pomdp_model.horizon))
            if self.pomdp_model
            else 0
        )
        rows: list[_Row] = []

        for option in options:
            commitment = commitment_score(
                option,
                model,
                commitments,
                self.commitment_weights,
                now,
                is_blocked,
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
            future = self._future_value(option, belief, horizon)
            blocker = _constraint_blocker(problem, option)
            total = round(
                commitment.utility
                + commitment.commitment
                + execution.execution
                + attention.human_attention
                + information
                + option_value
                + future,
                6,
            )
            score = CAVODScore(
                utility=commitment.utility,
                commitment=commitment.commitment,
                execution=execution.execution,
                human_attention=attention.human_attention,
                information=information,
                option=option_value,
                future=future,
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
                f"information {best.score.information:+.3f}, "
                f"option value {best.score.option:+.3f} and "
                f"future value {best.score.future:+.3f}"
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
                "future_value": best.score.future,
                "uncertainty": uncertainty,
                "belief": belief or None,
                "belief_entropy": belief_entropy(belief) if belief else None,
                "horizon": horizon if self.pomdp_model else None,
                "commitments_fulfilled": list(best.commitment.fulfilled),
                "commitments_violated": list(best.commitment.violated),
                "commitments_created": list(best.commitment.created),
                "receipt_status": best.execution.receipt_status,
                "approval_state": best.human_attention.effect.approval_state,
            },
        )

    def _resolve_belief(self, problem: PlannerInput) -> dict[str, float]:
        if self.pomdp_model is None:
            return {}
        raw = (problem.attributes or {}).get("belief")
        if isinstance(raw, Mapping):
            return normalize_belief(raw, self.pomdp_model.states)
        if self.belief:
            return normalize_belief(self.belief, self.pomdp_model.states)
        state = (problem.attributes or {}).get("state")
        if isinstance(state, str) and state:
            return belief_from_state(state, self.pomdp_model.states)
        size = len(self.pomdp_model.states)
        return {item: 1.0 / size for item in self.pomdp_model.states}

    def _action_for(self, option: ActionOption) -> str | None:
        if self.pomdp_model is None:
            return None
        if option.id in self.pomdp_model.actions:
            return option.id
        if option.verb in self.pomdp_model.actions:
            return option.verb
        return None

    def _future_value(
        self,
        option: ActionOption,
        belief: Mapping[str, float],
        horizon: int,
    ) -> float:
        if self.pomdp_model is None or not belief:
            return 0.0
        action = self._action_for(option)
        if action is None:
            return 0.0
        if not any(self.pomdp_model.action_available(state, action) for state in belief):
            return 0.0
        return round(
            self.weights.future
            * action_future_value(
                self.pomdp_model,
                belief,
                action,
                horizon=horizon,
            ),
            6,
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
                    "future": row.score.future,
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
