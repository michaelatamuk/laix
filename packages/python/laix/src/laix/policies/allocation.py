"""Allocation: choose a portfolio of work under a budget."""

from __future__ import annotations

from typing import Any

from ..decisions import Decision, Intent
from ._support import decision, number, value


class AllocationPolicy:
    name = "allocation.v1"
    version = "1.0"

    def decide(self, request: Any) -> list[Decision]:
        requests = tuple(value(request, "requests", ()) or ())
        budget = number(request, "budget", 0.0)
        max_risk = number(request, "max_risk", 1.0)

        candidates = [
            item
            for item in requests
            if float(item.get("cost", 0)) <= budget and float(item.get("risk", 0)) <= max_risk
        ]
        candidates.sort(
            key=lambda item: float(item.get("value", 0)) / max(float(item.get("cost", 0)), 0.001),
            reverse=True,
        )

        chosen: list[dict[str, Any]] = []
        spent = 0.0
        total_value = 0.0
        for item in candidates:
            cost = float(item.get("cost", 0))
            if spent + cost > budget:
                continue
            chosen.append(item)
            spent += cost
            total_value += float(item.get("value", 0))

        if not chosen:
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="nothing_affordable",
                    rationale="no request fits the budget and risk limit",
                    confidence=0.8,
                )
            ]
        return [
            decision(
                policy=self.name,
                verb="act",
                reason_code="allocate",
                rationale=f"fund {len(chosen)} request(s) for value {total_value:.2f} within budget {budget:.2f}",
                confidence=min(0.95, 0.5 + total_value / max(budget, 1.0) * 0.2),
                intent=Intent("allocate", {"ids": [str(item.get("id", "")) for item in chosen]}),
                score=round(total_value, 6),
                requires_approval=bool(value(request, "requires_approval", False)),
            )
        ]


__all__ = ["AllocationPolicy"]
