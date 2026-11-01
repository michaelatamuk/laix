"""Safety-constrained action: choose only inside the hard risk limit."""

from __future__ import annotations

from typing import Any

from ..decisions import Decision, Intent
from ._support import decision, number, value


class SafetyConstrainedPolicy:
    name = "safety-constrained.v1"
    version = "0.6.0"

    def decide(self, request: Any) -> list[Decision]:
        if bool(value(request, "safety_blocked", False)):
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="safety_blocked",
                    rationale="a hard safety constraint blocks action",
                    confidence=1.0,
                )
            ]

        risk_limit = number(request, "risk_limit", 0.2)
        options = tuple(value(request, "options", ()) or ())
        safe = [item for item in options if float(item.get("risk", 0)) <= risk_limit]
        if not safe:
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="no_safe_option",
                    rationale="every available option exceeds the risk limit",
                    confidence=0.9,
                )
            ]

        best = max(
            safe,
            key=lambda item: float(item.get("benefit", 0))
            - float(item.get("risk", 0))
            - 0.1 * float(item.get("cost", 0)),
        )
        benefit = float(best.get("benefit", 0))
        risk = float(best.get("risk", 0))
        requires_approval = bool(best.get("requires_approval", False) or best.get("destructive", False))
        return [
            decision(
                policy=self.name,
                verb="act" if benefit >= 0.5 else "guide",
                reason_code="safe_action" if benefit >= 0.5 else "safe_to_show",
                rationale=f"choose {best.get('id', '?')} with risk {risk:.2f} inside the limit {risk_limit:.2f}",
                confidence=min(0.98, 0.55 + benefit * 0.4),
                intent=Intent("act", {"id": str(best.get("id", ""))}),
                score=round(benefit - risk, 6),
                requires_approval=requires_approval,
                action_id=str(best.get("id", "")),
            )
        ]


__all__ = ["SafetyConstrainedPolicy"]
