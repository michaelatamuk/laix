"""Author a rule policy and wrap it with a group target."""

from __future__ import annotations

from laix import DecisionRequest, Rule, RulePolicy, TargetedPolicy

policy = TargetedPolicy(
    RulePolicy(
        [
            Rule(when={"amount": {"gte": 500}}, verb="ask", reason_code="over_limit"),
            Rule(when={"priority": "high"}, verb="act", reason_code="priority"),
        ]
    ),
    target="some",
    recipients=("alice", "ben"),
)
decision = policy.decide(
    DecisionRequest(
        subject="refund",
        at="2026-11-01T10:00:00+00:00",
        attributes={"amount": 780},
    )
)[0]
print(decision.verb, decision.reason_code, decision.target, decision.recipients)
