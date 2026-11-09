"""Declarative rules and the target wrapper."""

from __future__ import annotations

from laix import DecisionRequest, Rule, RulePolicy, TargetedPolicy


def _request(**attributes: object) -> DecisionRequest:
    return DecisionRequest(
        subject="a task",
        at="2026-11-01T10:00:00+00:00",
        attributes=dict(attributes),
    )


def test_rule_policy_matches_a_threshold() -> None:
    policy = RulePolicy(
        [
            Rule(
                when={"amount": {"gte": 500}},
                verb="ask",
                reason_code="over_limit",
                rationale="the amount needs approval",
            ),
            Rule(
                when={"priority": "high"},
                verb="act",
                reason_code="priority",
            ),
        ]
    )

    decision = policy.decide(_request(amount=780))[0]
    assert decision.verb == "ask"
    assert decision.reason_code == "over_limit"
    assert decision.policy_version == "rules.v1"


def test_rule_policy_falls_back_when_nothing_matches() -> None:
    policy = RulePolicy([Rule(when={"amount": {"gte": 500}}, verb="ask", reason_code="over_limit")])
    decision = policy.decide(_request(amount=10))[0]

    assert decision.verb == "wait"
    assert decision.reason_code == "no_rule"


def test_targeted_policy_copies_mode_and_recipients() -> None:
    policy = TargetedPolicy(
        RulePolicy([Rule(when={}, verb="guide", reason_code="share")]),
        target="some",
        recipients=("alice", "ben"),
    )
    decision = policy.decide(_request())[0]

    assert decision.target == "some"
    assert decision.recipients == ("alice", "ben")


def test_targeted_policy_can_take_the_target_from_the_request() -> None:
    policy = TargetedPolicy(RulePolicy([Rule(when={}, verb="guide", reason_code="share")]))
    decision = policy.decide(
        DecisionRequest(
            subject="a task",
            at="2026-11-01T10:00:00+00:00",
            target="all",
            recipients=("group",),
        )
    )[0]

    assert decision.target == "all"
    assert decision.recipients == ("group",)
