"""Shadow a second policy without changing the primary decision."""

from __future__ import annotations

from laix import DecisionRequest, Rule, RulePolicy, ShadowPolicy

primary = RulePolicy([Rule(when={"amount": {"gte": 500}}, verb="ask", reason_code="over_limit")])
shadow = RulePolicy([Rule(when={"amount": {"gte": 500}}, verb="act", reason_code="over_limit")])
policy = ShadowPolicy(primary, shadow)

decision = policy.decide(
    DecisionRequest(
        subject="refund",
        at="2026-11-01T10:00:00+00:00",
        attributes={"amount": 780},
    )
)[0]
print(decision.verb, len(policy.differences), policy.differences[0].shadow[0].verb)
