"""Reuse a similar past decision when no model is available."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ...contract.planner import Planner
from ...contract.planner_policy import PlannerInput, PlannerResult


@dataclass(frozen=True, slots=True)
class PastDecision:
    """One observed subject, action and outcome."""

    subject: str
    action_id: str
    verb: str = "act"
    attributes: dict[str, Any] = field(default_factory=dict)


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _similarity(problem: PlannerInput, case: PastDecision) -> float:
    wanted = _tokens(problem.subject)
    found = _tokens(case.subject)
    token = (
        len(wanted & found) / len(wanted | found)
        if wanted and found
        else 0.0
    )
    action = 1.0 if case.action_id in {option.id for option in problem.options} else 0.0
    return round(0.7 * token + 0.3 * action, 6)


class CaseBasedPlanner:
    """Choose the action from the most similar past decision."""

    name = "case_based.v1"

    def __init__(
        self,
        cases: Sequence[PastDecision],
        *,
        fallback: Planner | None = None,
        threshold: float = 0.2,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between zero and one")
        self.cases = tuple(cases)
        self.fallback = fallback
        self.threshold = threshold

    def solve(self, problem: PlannerInput) -> PlannerResult:
        scored = sorted(
            (
                (_similarity(problem, case), case)
                for case in self.cases
            ),
            key=lambda item: (-item[0], item[1].subject, item[1].action_id),
        )
        if scored and scored[0][0] >= self.threshold:
            similarity, case = scored[0]
            return PlannerResult(
                verb=case.verb,  # type: ignore[arg-type]
                confidence=similarity,
                reason_code="case_based",
                rationale=f"{case.subject} is the closest past decision",
                action_id=case.action_id,
                attributes={
                    "case_subject": case.subject,
                    "case_similarity": similarity,
                    **dict(case.attributes),
                },
            )
        if self.fallback is not None:
            return self.fallback.solve(problem)
        return PlannerResult(
            verb="wait",
            confidence=1.0,
            reason_code="no_case",
            rationale="no similar past decision",
            score=0.0,
        )


__all__ = ["CaseBasedPlanner", "PastDecision"]
