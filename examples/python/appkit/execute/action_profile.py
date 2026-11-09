"""Map an OpenAPI action-profile request onto an execution receipt."""

from __future__ import annotations

from laix import ActionOption, Decision, ExecutionBridge

profile_request = {
    "decision_id": "DEC-1",
    "trace_id": "TRC-1",
    "actor": "incident-bot",
    "approver": "alice",
    "context": {"case_id": "C-1042"},
}

decision = Decision(
    verb="act",
    confidence=0.9,
    reason_code="safe_action",
    rationale="the action is approved",
    decision_id=profile_request["decision_id"],
    trace_id=profile_request["trace_id"],
    action_id="close",
    requires_approval=True,
)
action = ActionOption(id="close", verb="act", name="close case")

bridge = ExecutionBridge(
    handlers={"close case": lambda action, context: {"closed": context["case_id"]}}
)
receipt = bridge.execute(
    decision,
    action=action,
    actor=profile_request["actor"],
    approver=profile_request["approver"],
    context=profile_request["context"],
)

print(receipt.status, receipt.action_name)
