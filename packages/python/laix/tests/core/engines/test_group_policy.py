"""Group policy: target and private-state masking."""

from __future__ import annotations

from laix import Decision, DecisionRequest, GroupPolicy


class FakePolicy:
    def decide(self, request: DecisionRequest) -> list[Decision]:
        return [
            Decision(
                verb="guide",
                confidence=0.9,
                reason_code="share",
                rationale="share",
                attributes={"topic": "math", "health": "private"},
            )
        ]


def test_group_policy_sets_the_target_and_masks_private_state() -> None:
    policy = GroupPolicy(
        FakePolicy(),
        target="all",
        recipients=("alice", "ben", "chris"),
        private_attributes=("health",),
    )
    decision = policy.decide(DecisionRequest(subject="a task", at="2026-11-01T10:00:00+00:00"))[0]

    assert decision.target == "all"
    assert decision.recipients == ("alice", "ben", "chris")
    assert decision.attributes == {"topic": "math"}
