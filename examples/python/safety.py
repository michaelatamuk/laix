"""Two options, one risk limit. Choose only what is safe.

The result is:

    act safe_action valve

- act: do something now.
- safe_action: the chosen option sits inside the risk limit.
- valve: the safe option; the higher-benefit option is too risky.
"""

from laix import DecisionRequest, Layer, SafetyConstrainedPolicy, iso

decision = Layer(policy=SafetyConstrainedPolicy()).decide(
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

print(decision.verb, decision.reason_code, decision.action_id)
