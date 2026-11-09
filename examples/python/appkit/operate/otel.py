"""Map one decision onto OpenTelemetry attribute names."""

from __future__ import annotations

from laix import Decision, decision_attributes

decision = Decision(
    verb="act",
    confidence=0.92,
    reason_code="safe_action",
    rationale="the valve is inside the risk limit",
    decision_id="DEC-1",
    trace_id="TRC-1",
    policy_version="live.v1",
    action_id="valve",
    requires_approval=True,
)

attributes = decision_attributes(decision)
print(
    attributes["laix.verb"],
    attributes["laix.reason_code"],
    attributes["laix.action.id"],
    attributes["laix.approval.required"],
)
