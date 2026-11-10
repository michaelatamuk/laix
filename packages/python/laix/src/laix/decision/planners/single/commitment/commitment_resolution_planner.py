"""Turn a blocked commitment decision into a verification decision."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from ....contract.planner_policy import PlannerInput, PlannerResult
from ....domain.decisions import Intent
from ..utility.utility_planner import UtilityModel
from .commitment_planner import (
    CommitmentPlanner,
    CommitmentWeights,
    _active_and_graph,
    _now,
    _option_blockers,
)

_MODES = ("verify", "ask")


class CommitmentResolutionPlanner:
    """Resolve blocked hard commitments with a concrete next step.

    The planner runs the normal commitment planner first. When every option is
    blocked, it returns ``verify`` (or ``ask`` when configured) with the
    owner-qualified references that must be resolved.
    """

    name = "commitment.resolution.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        weights: CommitmentWeights | None = None,
        *,
        require_verified: bool = True,
        max_verification_age: timedelta | None = None,
        mode: str = "verify",
    ) -> None:
        if mode not in _MODES:
            raise ValueError(f"unknown commitment resolution mode: {mode}")
        self.mode = mode
        self._planner = CommitmentPlanner(
            model,
            weights,
            require_verified=require_verified,
            max_verification_age=max_verification_age,
        )

    def solve(self, problem: PlannerInput) -> PlannerResult:
        base = self._planner.solve(problem)
        if base.reason_code == "no_options" or base.verb != "wait":
            return base

        active, graph = _active_and_graph(problem)
        now = _now(problem)
        found: dict[tuple[str, str, str], dict[str, Any]] = {}
        for option in problem.options:
            for blocker in _option_blockers(
                option,
                active,
                graph,
                self._planner.require_verified,
                now,
                self._planner.max_verification_age,
            ):
                found[
                    (
                        str(blocker["owner"]),
                        str(blocker["ledger"] or ""),
                        str(blocker["id"]),
                    )
                ] = blocker
        if not found:
            return base

        refs = [found[key] for key in sorted(found)]
        verb = "ask" if self.mode == "ask" else "verify"
        return PlannerResult(
            verb=verb,
            confidence=0.8,
            reason_code="commitment_resolution",
            rationale=(
                f"resolve {len(refs)} blocked commitment "
                f"{'dependency' if len(refs) == 1 else 'dependencies'}"
            ),
            action_id="resolve-commitments",
            intent=Intent(
                capability="verify_commitment",
                args={"refs": refs},
            ),
            requires_approval=verb == "ask",
            reversible=True,
            attributes={
                "verification_refs": refs,
                "blocked_by": refs,
                "base_reason_code": base.reason_code,
            },
        )


__all__ = ["CommitmentResolutionPlanner"]
