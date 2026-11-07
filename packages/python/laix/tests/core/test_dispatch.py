"""The core dispatch path: one request in, one identified decision out."""

from __future__ import annotations

from datetime import datetime, timezone

from laix.core import ActionOption, Decision, DecisionRequest, Situation, decide
from laix.core.engines.signals import SignalContext, Signal


def at(hour: int = 10) -> datetime:
    return datetime(2026, 11, 2, hour, tzinfo=timezone.utc)


def action_request() -> DecisionRequest:
    return DecisionRequest(
        subject="room-1",
        at=at().isoformat(),
        situation=Situation(id="s-1", at=at().isoformat(), subject="room-1"),
        options=(ActionOption(id="a-1", verb="wait", name="wait"),),
    )


def test_action_decisions_carry_ids() -> None:
    decision = decide(action_request())[0]
    assert decision.decision_id.startswith("DEC-")
    assert decision.trace_id.startswith("TRC-")


def test_a_host_can_supply_the_id_factory() -> None:
    decision = decide(action_request(), id_factory=lambda prefix: f"{prefix}-fixed")[0]
    assert decision.decision_id == "DEC-fixed"
    assert decision.trace_id == "TRC-fixed"


def test_a_policy_decision_without_ids_gets_them() -> None:
    class AlwaysWait:
        name = "always-wait"
        version = "1.0"

        def decide(self, request):
            return [
                Decision(
                    verb="wait",
                    confidence=0.5,
                    reason_code="policy_rule",
                    rationale="this policy always waits",
                )
            ]

    decision = decide(action_request(), policy=AlwaysWait())[0]
    assert decision.verb == "wait"
    assert decision.decision_id.startswith("DEC-")
    assert decision.trace_id.startswith("TRC-")


def test_attention_decisions_keep_their_trace_id_and_get_a_decision_id() -> None:
    signal = Signal(id="s-1", kind="power", severity="high", confidence=0.9)
    request = DecisionRequest(
        subject="room-1",
        at=at().isoformat(),
        signals=(signal,),
        context=SignalContext(now=at(), quiet_hours=None),
    )
    decision = decide(request)[0]
    assert decision.trace_id
    assert decision.decision_id.startswith("DEC-")
