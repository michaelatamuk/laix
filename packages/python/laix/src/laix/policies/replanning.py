"""Replanning: choose a plan after the old one broke."""

from __future__ import annotations

from typing import Any

from ..decisions import Decision, Intent
from ._support import decision, number, value


class ReplanningPolicy:
    name = "replanning.v1"
    version = "0.6.0"

    def decide(self, request: Any) -> list[Decision]:
        plans = tuple(value(request, "plans", ()) or ())
        min_success = number(request, "min_success", 0.5)
        max_cost = number(request, "max_cost", float("inf"))
        risk_weight = number(request, "risk_weight", 1.0)

        feasible = [
            plan
            for plan in plans
            if float(plan.get("success_probability", 0)) >= min_success
            and float(plan.get("cost", 0)) <= max_cost
        ]
        if not feasible:
            return [
                decision(
                    policy=self.name,
                    verb="ask",
                    reason_code="no_feasible_plan",
                    rationale="no plan meets the success and cost limits; ask for a changed constraint",
                    confidence=0.8,
                )
            ]

        best = max(
            feasible,
            key=lambda plan: float(plan.get("success_probability", 0))
            - risk_weight * float(plan.get("cost", 0))
            - float(plan.get("deadline_risk", 0)),
        )
        success = float(best.get("success_probability", 0))
        return [
            decision(
                policy=self.name,
                verb="act",
                reason_code="replan",
                rationale=f"adopt {best.get('id', '?')} with success probability {success:.2f}",
                confidence=min(0.98, 0.5 + success * 0.4),
                intent=Intent("adopt_plan", {"id": str(best.get("id", ""))}),
                score=success,
                requires_approval=bool(best.get("requires_approval", False)),
                action_id=str(best.get("id", "")),
            )
        ]


__all__ = ["ReplanningPolicy"]
