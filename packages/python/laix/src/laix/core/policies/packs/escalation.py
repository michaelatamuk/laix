"""Escalation: decide when a situation must leave the current owner.

Escalation is a decision class, not only a lifecycle phase. It fires on severity,
repeated attempts, low confidence or a breached service level, and it names the
target that should take over.
"""

from __future__ import annotations

from typing import Any

from ...decisions import Decision, Escalation
from .._support import decision, number, value


class EscalationPolicy:
    name = "escalation.v1"
    version = "0.8.0"

    def decide(self, request: Any) -> list[Decision]:
        if bool(value(request, "resolved", False)):
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="resolved",
                    rationale="the situation is resolved; no escalation is needed",
                    confidence=1.0,
                )
            ]

        severity = number(request, "severity", 0.0)
        threshold = number(request, "severity_threshold", 0.8)
        attempts = int(number(request, "attempts", 0))
        max_attempts = int(number(request, "max_attempts", 3))
        confidence = number(request, "confidence", 1.0)
        min_confidence = number(request, "min_confidence", 0.5)
        sla_breached = bool(value(request, "sla_breached", False))

        reasons: list[str] = []
        if severity >= threshold:
            reasons.append(f"severity {severity:.2f} reached {threshold:.2f}")
        if attempts >= max_attempts:
            reasons.append(f"attempts {attempts} reached {max_attempts}")
        if confidence < min_confidence:
            reasons.append(f"confidence {confidence:.2f} is below {min_confidence:.2f}")
        if sla_breached:
            reasons.append("the service level is breached")

        if not reasons:
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="within_limits",
                    rationale="severity, attempts and confidence are still within limits",
                    confidence=confidence,
                )
            ]

        target = str(value(request, "target", "") or "")
        rationale = "; ".join(reasons)
        if not target:
            return [
                decision(
                    policy=self.name,
                    verb="ask",
                    reason_code="target_required",
                    rationale=f"{rationale}; no escalation target is known",
                    confidence=0.7,
                )
            ]

        return [
            decision(
                policy=self.name,
                verb="escalate",
                reason_code="escalate_to_target",
                rationale=f"{rationale}; hand over to {target}",
                confidence=min(0.98, max(severity, 1.0 - confidence)),
                escalation=Escalation(target=target, reason=rationale),
                score=round(severity, 6),
                action_id=target,
            )
        ]


__all__ = ["EscalationPolicy"]
