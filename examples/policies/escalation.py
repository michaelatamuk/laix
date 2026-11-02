"""The situation is too severe for the current owner. Hand it over.

The result is:

    escalate escalate_to_target manager

- escalate: leave the current owner.
- escalate_to_target: a named target takes over.
- manager: the target.
"""

from laix import DecisionRequest, EscalationPolicy, Layer, iso

decision = Layer(policy=EscalationPolicy()).decide(
    DecisionRequest(
        subject="production incident",
        at=iso(),
        attributes={
            "severity": 0.9,
            "severity_threshold": 0.8,
            "target": "manager",
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
