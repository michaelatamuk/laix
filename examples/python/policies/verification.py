"""An action ran. Confirm the outcome before trusting it.

The result is:

    verify verify_outcome api

- verify: run a check.
- verify_outcome: the check confirms what the action claimed.
- api: the check with the best confidence gain per cost.
"""

from laix import DecisionRequest, Layer, VerificationPolicy, iso

decision = Layer(policy=VerificationPolicy()).decide(
    DecisionRequest(
        subject="payment sent",
        at=iso(),
        attributes={
            "confidence": 0.4,
            "required_confidence": 0.8,
            "checks": [
                {"id": "manual", "confidence_gain": 0.2, "cost": 1},
                {"id": "api", "confidence_gain": 0.8, "cost": 1},
            ],
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
