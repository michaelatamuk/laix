"""Plan with an explicit completion probability for external promises."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from ....contract.planner_policy import PlannerInput, PlannerResult
from ....domain.commitments import CommitmentGraph, CommitmentRef
from ....domain.decisions import Intent
from ....support.values import clamp
from ..utility.utility_planner import UtilityModel, UtilityPlanner
from .commitment_planner import (
    _active_and_graph,
    _now,
    commitment_effect,
)


def _probability_key(ref: CommitmentRef) -> str:
    return f"{ref.owner}/{ref.ledger or ''}/{ref.id}"


class CommitmentBeliefPlanner:
    """Weight an option by the chance its external dependencies complete.

    Completion probabilities come from ``attributes["commitment_probabilities"]``
    (keyed by ``owner/ledger/id``, ``owner:id`` or plain id), then from the
    commitment's ``payload["completion_probability"]``, then from
    ``default_probability``. Trusted and verified promises count as certain.
    """

    name = "commitment_belief.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        *,
        default_probability: float = 0.5,
        verify_below: float = 0.7,
        require_verified: bool = True,
        max_verification_age: timedelta | None = None,
    ) -> None:
        if not 0.0 <= default_probability <= 1.0:
            raise ValueError("default_probability must be between zero and one")
        if not 0.0 <= verify_below <= 1.0:
            raise ValueError("verify_below must be between zero and one")
        self.model = model or UtilityModel()
        self.default_probability = default_probability
        self.verify_below = verify_below
        self.require_verified = require_verified
        self.max_verification_age = max_verification_age
        self._utility = UtilityPlanner(self.model)

    def _probability(
        self,
        ref: CommitmentRef,
        graph: CommitmentGraph,
        attributes: dict[str, Any],
        now,
    ) -> float:
        item = graph.get(ref)
        if item is None:
            return 0.0
        trusted = (
            item.status == "done"
            and item.trusted
            and (
                self.max_verification_age is None
                or graph.is_fresh(item, now, self.max_verification_age)
            )
        )
        if trusted:
            return 1.0
        explicit = attributes.get("commitment_probabilities")
        if isinstance(explicit, dict):
            for key in (
                _probability_key(ref),
                f"{ref.owner}:{ref.id}",
                ref.id,
            ):
                if key in explicit:
                    return clamp(float(explicit[key]))
        payload_value = item.payload.get("completion_probability")
        if payload_value is not None:
            return clamp(float(payload_value))
        return self.default_probability

    def solve(self, problem: PlannerInput) -> PlannerResult:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        active, graph = _active_and_graph(problem)
        attributes = problem.attributes or {}
        now = _now(problem)
        rows: list[dict[str, Any]] = []
        for option in options:
            utility = model.score(option)
            effect = commitment_effect(option)
            refs: list[CommitmentRef] = []
            for commitment_id in effect.fulfills:
                commitment = active.get(commitment_id)
                if commitment is None:
                    continue
                refs.extend(graph.dependencies(commitment))
            refs = list(dict.fromkeys(refs))
            if refs:
                probability = min(
                    self._probability(ref, graph, attributes, now) for ref in refs
                )
            else:
                probability = 1.0
            expected = round(utility * probability, 6)
            rows.append(
                {
                    "option": option,
                    "utility": round(utility, 6),
                    "probability": round(probability, 6),
                    "expected": expected,
                    "refs": refs,
                    "feasible": model.feasible(option),
                }
            )

        feasible = [row for row in rows if row["feasible"]]
        if not feasible:
            return self._wait(
                "no_feasible_option", "every option breaks a hard limit"
            )

        feasible.sort(key=lambda row: (-row["expected"], row["option"].id))
        best = feasible[0]
        second = feasible[1]["expected"] if len(feasible) > 1 else None
        if best["probability"] < self.verify_below and best["refs"]:
            refs = [
                {
                    "owner": ref.owner,
                    "ledger": ref.ledger,
                    "id": ref.id,
                    "reason": "uncertain",
                }
                for ref in best["refs"]
            ]
            return PlannerResult(
                verb="verify",
                confidence=clamp(1.0 - best["probability"]),
                reason_code="commitment_belief_verify",
                rationale=(
                    f"{best['option'].id} depends on a promise with "
                    f"completion probability {best['probability']:.3f}"
                ),
                action_id="resolve-commitments",
                intent=Intent(capability="verify_commitment", args={"refs": refs}),
                reversible=True,
                attributes={
                    "completion_probability": best["probability"],
                    "verification_refs": refs,
                },
            )

        alternatives = tuple(
            {
                "action_id": row["option"].id,
                "verb": row["option"].verb,
                "name": row["option"].name,
                "utility": row["utility"],
                "completion_probability": row["probability"],
                "expected_utility": row["expected"],
                "rejected_reason_code": (
                    "lower_expected_utility"
                    if row["feasible"]
                    else "outside_hard_limits"
                ),
            }
            for row in rows
            if row["option"].id != best["option"].id
        )
        return PlannerResult(
            verb=best["option"].verb,
            confidence=self._confidence(best["expected"], second),
            reason_code="commitment_belief",
            rationale=(
                f"{best['option'].id} has expected utility {best['expected']:.3f} "
                f"at completion probability {best['probability']:.3f}"
            ),
            action_id=best["option"].id,
            requires_approval=bool(best["option"].requires_approval),
            reversible=best["option"].reversible,
            score=best["expected"],
            alternatives=alternatives,
            attributes={
                "utility": best["utility"],
                "completion_probability": best["probability"],
                "expected_utility": best["expected"],
            },
        )

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


__all__ = ["CommitmentBeliefPlanner"]
