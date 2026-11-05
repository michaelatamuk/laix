"""Group decisions: a target, recipients and private-state masking."""

from __future__ import annotations

from laix import Decision, DecisionRequest, GroupPolicy


class SharePolicy:
    def decide(self, request: DecisionRequest) -> list[Decision]:
        return [
            Decision(
                verb="guide",
                confidence=0.9,
                reason_code="share",
                rationale="share the lesson",
                attributes={"topic": "math", "health": "private"},
            )
        ]


policy = GroupPolicy(
    SharePolicy(),
    target="all",
    recipients=("alice", "ben", "chris"),
    private_attributes=("health",),
)
decision = policy.decide(
    DecisionRequest(subject="a task", at="2026-11-01T10:00:00+00:00")
)[0]
print(decision.target, decision.recipients, decision.attributes)
