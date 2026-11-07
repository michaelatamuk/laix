"""One request shape, two generic policies, one decision shape."""

from __future__ import annotations

from datetime import datetime, timezone

from laix import (
    ActionOption,
    Belief,
    SignalContext,
    DecisionRequest,
    DecisionClient,
    Signal,
    Situation,
    iso,
)


def test_attention_request_returns_the_one_decision_shape() -> None:
    layer = DecisionClient()
    decisions = layer.decide(
        DecisionRequest(
            subject="one signal",
            at="2026-11-01T10:00:00+00:00",
            signals=(Signal(id="s-1", kind="k", severity="high", confidence=0.9),),
            context=SignalContext(now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc), quiet_hours=None),
        )
    )
    assert len(decisions) == 1
    assert decisions[0].verb in {"guide", "ask", "act", "escalate", "wait"}
    assert decisions[0].reason_code
    assert decisions[0].to_dict()["verb"] == decisions[0].verb


def test_action_request_returns_the_same_shape() -> None:
    layer = DecisionClient()
    situation = Situation(
        id="sit-1",
        at=iso(),
        subject="one situation",
        beliefs=(Belief(id="b", proposition="the condition is real", confidence=0.9),),
        attributes={"urgency": 0.9},
    )
    options = (
        ActionOption(id="a-wait", verb="wait", name="keep_observing", expected_benefit=0.2),
        ActionOption(id="a-act", verb="act", name="apply_change", expected_benefit=0.9),
    )
    decisions = layer.decide(
        DecisionRequest(subject="one situation", at=iso(), situation=situation, options=options)
    )
    assert len(decisions) == 1
    assert decisions[0].verb in {"wait", "observe", "guide", "ask", "act", "verify", "escalate"}
    assert decisions[0].reason_code == "policy_rule"


def test_decision_client_exposes_a_stream_session() -> None:
    layer = DecisionClient()
    stream = layer.stream(stream_id="STR-1", capacity=2)
    decisions = stream.observe(
        DecisionRequest(
            subject="one signal",
            at="2026-11-01T10:00:00+00:00",
            signals=(Signal(id="s-1", kind="k", severity="high", confidence=0.9),),
            context=SignalContext(now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc), quiet_hours=None),
        )
    )

    assert len(decisions) == 1
    assert decisions[0].stream_id == "STR-1"
    assert decisions[0].status == "final"
