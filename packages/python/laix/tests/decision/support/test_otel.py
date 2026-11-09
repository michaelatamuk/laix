"""OpenTelemetry attribute mapping."""

from __future__ import annotations

from laix import Decision, decision_attributes


def test_decision_attributes_use_stable_names() -> None:
    decision = Decision(
        verb="act",
        confidence=0.8,
        reason_code="safe_action",
        rationale="inside the limit",
        decision_id="DEC-1",
        trace_id="TRC-1",
        policy_version="live.v1",
        action_id="valve",
        requires_approval=True,
        score=0.91,
        stream_id="stream-1",
        revision=2,
        supersedes="DEC-0",
    )

    attributes = decision_attributes(decision)

    assert attributes["laix.verb"] == "act"
    assert attributes["laix.reason_code"] == "safe_action"
    assert attributes["laix.decision.id"] == "DEC-1"
    assert attributes["laix.trace.id"] == "TRC-1"
    assert attributes["laix.policy.version"] == "live.v1"
    assert attributes["laix.action.id"] == "valve"
    assert attributes["laix.confidence"] == 0.8
    assert attributes["laix.approval.required"] is True
    assert attributes["laix.score"] == 0.91
    assert attributes["laix.stream.id"] == "stream-1"
    assert attributes["laix.revision"] == 2
    assert attributes["laix.supersedes"] == "DEC-0"
    assert attributes["laix.schema.version"]


def test_decision_attributes_skip_empty_optional_fields() -> None:
    decision = Decision(
        verb="wait",
        confidence=0.5,
        reason_code="no_options",
        rationale="nothing to do",
    )

    attributes = decision_attributes(decision)

    assert "laix.decision.id" not in attributes
    assert "laix.action.id" not in attributes
    assert "laix.score" not in attributes
    assert "laix.revision" not in attributes
