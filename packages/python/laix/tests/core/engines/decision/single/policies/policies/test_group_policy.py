"""Group policy: target and private-state masking."""

from __future__ import annotations

from types import SimpleNamespace

from laix import Decision, DecisionRequest, EvidenceRef, GroupPolicy, Intent


def _fake_policy() -> SimpleNamespace:
    def decide(request: DecisionRequest) -> list[Decision]:
        return [
            Decision(
                verb="guide",
                confidence=0.9,
                reason_code="share",
                rationale="share",
                attributes={"topic": "math", "health": "private"},
            )
        ]

    return SimpleNamespace(decide=decide)


def _rich_policy() -> SimpleNamespace:
    def decide(request: DecisionRequest) -> list[Decision]:
        return [
            Decision(
                verb="guide",
                confidence=0.9,
                reason_code="share",
                rationale="the health record is private",
                evidence=(
                    EvidenceRef(id="e1", kind="note", source="health"),
                    EvidenceRef(id="e2", kind="note", source="catalog"),
                ),
                intent=Intent("share", {"health": "private", "topic": "math"}),
                undo_hint="health record",
                alternatives=({"health": "private", "ok": 1},),
                attributes={
                    "topic": "math",
                    "nested": {"health": "private", "visible": 1},
                    "items": [{"health": "private", "ok": 2}],
                },
            )
        ]

    return SimpleNamespace(decide=decide)


def test_group_policy_sets_the_target_and_masks_private_state() -> None:
    policy = GroupPolicy(
        _fake_policy(),
        target="all",
        recipients=("alice", "ben", "chris"),
        private_attributes=("health",),
    )
    decision = policy.decide(DecisionRequest(subject="a task", at="2026-11-01T10:00:00+00:00"))[0]

    assert decision.target == "all"
    assert decision.recipients == ("alice", "ben", "chris")
    assert decision.attributes == {"topic": "math"}


def test_group_policy_masks_nested_attributes_evidence_and_rationale() -> None:
    policy = GroupPolicy(
        _rich_policy(),
        private_attributes=("health",),
        private_evidence=("health",),
        rationale="shared summary",
        undo_hint="shared undo",
    )
    decision = policy.decide(
        DecisionRequest(subject="a task", at="2026-11-01T10:00:00+00:00")
    )[0]

    assert decision.rationale == "shared summary"
    assert decision.undo_hint == "shared undo"
    assert [item.id for item in decision.evidence] == ["e2"]
    assert decision.intent is not None
    assert decision.intent.args == {"topic": "math"}
    assert decision.alternatives == ({"ok": 1},)
    assert decision.attributes == {
        "topic": "math",
        "nested": {"visible": 1},
        "items": [{"ok": 2}],
    }
