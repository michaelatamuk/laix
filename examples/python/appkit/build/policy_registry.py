"""Register a policy with the app-kit client and switch to it."""

from __future__ import annotations

from laix import DecisionClient, DecisionRequest, SafetyConstrainedPolicy, iso

client = DecisionClient()
client.register_policy("safety", SafetyConstrainedPolicy())
client.use_policy("safety")

decision = client.decide(
    DecisionRequest(
        subject="leaking sink",
        at=iso(),
        attributes={
            "risk_limit": 0.2,
            "options": [
                {"id": "valve", "benefit": 0.9, "risk": 0.1},
                {"id": "hit-pipe", "benefit": 1.0, "risk": 0.9},
            ],
        },
    )
)[0]

print(",".join(client.policies()), decision.verb, decision.action_id)
