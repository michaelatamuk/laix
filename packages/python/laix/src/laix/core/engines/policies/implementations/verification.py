"""Verification: confirm that an action did what it claimed.

Verification is a decision class, not only a lifecycle phase. After an action,
the layer decides whether to check, which check to run, or whether no check is
possible and a person must confirm.
"""

from __future__ import annotations

from typing import Any

from ....decisions import Decision, Intent
from ._helpers import decision, number, value


class VerificationPolicy:
    name = "verification.v1"
    version = "0.8.0"

    def decide(self, request: Any) -> list[Decision]:
        if bool(value(request, "verified", False)):
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="already_verified",
                    rationale="the outcome is already confirmed",
                    confidence=1.0,
                )
            ]

        confidence = number(request, "confidence", 0.5)
        required = number(request, "required_confidence", 0.8)
        due = value(request, "verification_due", True)
        budget = number(request, "budget", float("inf"))
        checks = tuple(value(request, "checks", ()) or ())

        if not due and confidence >= required:
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="verification_not_needed",
                    rationale=f"confidence {confidence:.2f} meets the requirement {required:.2f}",
                    confidence=confidence,
                )
            ]

        if not checks:
            return [
                decision(
                    policy=self.name,
                    verb="escalate",
                    reason_code="no_verification_path",
                    rationale="no check can confirm the outcome; ask a person",
                    confidence=0.6,
                    intent=Intent(
                        "handover",
                        {
                            "target": str(value(request, "escalation_target", "human")),
                            "reason": "no verification path",
                        },
                    ),
                )
            ]

        affordable = [item for item in checks if float(item.get("cost", 0)) <= budget]
        if not affordable:
            return [
                decision(
                    policy=self.name,
                    verb="escalate",
                    reason_code="no_verification_budget",
                    rationale="every check costs more than the verification budget",
                    confidence=0.6,
                    intent=Intent(
                        "handover",
                        {
                            "target": str(value(request, "escalation_target", "human")),
                            "reason": "verification budget exhausted",
                        },
                    ),
                )
            ]

        best = max(
            affordable,
            key=lambda item: float(item.get("confidence_gain", item.get("information_gain", 0)))
            / max(float(item.get("cost", 0)), 0.001),
        )
        gain = float(best.get("confidence_gain", best.get("information_gain", 0)))
        if gain <= 0:
            return [
                decision(
                    policy=self.name,
                    verb="escalate",
                    reason_code="no_verification_path",
                    rationale="no available check would raise confidence",
                    confidence=0.6,
                    intent=Intent(
                        "handover",
                        {
                            "target": str(value(request, "escalation_target", "human")),
                            "reason": "no useful verification path",
                        },
                    ),
                )
            ]

        return [
            decision(
                policy=self.name,
                verb="verify",
                reason_code="verify_outcome",
                rationale=f"run check {best.get('id', '?')} to confirm the outcome",
                confidence=min(0.95, confidence + gain),
                intent=Intent("verify", {"id": str(best.get("id", ""))}),
                score=round(gain, 6),
                action_id=str(best.get("id", "")),
            )
        ]


__all__ = ["VerificationPolicy"]
