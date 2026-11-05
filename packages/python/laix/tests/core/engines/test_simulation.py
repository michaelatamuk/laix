"""Policy simulation and shadow mode."""

from __future__ import annotations

from laix import DecisionRequest, Rule, RulePolicy, ShadowPolicy, simulate


def _request(amount: int) -> DecisionRequest:
    return DecisionRequest(
        subject="a task",
        at="2026-11-01T10:00:00+00:00",
        attributes={"amount": amount},
    )


def test_simulate_runs_a_policy_offline() -> None:
    policy = RulePolicy([Rule(when={"amount": {"gte": 500}}, verb="ask", reason_code="over_limit")])
    decisions = simulate(policy, [_request(100), _request(700)])

    assert [item[0].verb for item in decisions] == ["wait", "ask"]


def test_shadow_policy_returns_primary_and_records_differences() -> None:
    primary = RulePolicy([Rule(when={"amount": {"gte": 500}}, verb="ask", reason_code="over_limit")])
    shadow = RulePolicy([Rule(when={"amount": {"gte": 500}}, verb="act", reason_code="over_limit")])
    policy = ShadowPolicy(primary, shadow)

    decision = policy.decide(_request(700))[0]
    assert decision.verb == "ask"
    assert len(policy.differences) == 1
    assert policy.differences[0].shadow[0].verb == "act"
