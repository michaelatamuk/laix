"""Uncertainty is high. Look before deciding.

The result is:

    observe observe_for_information look-1

- observe: take one more observation before choosing.
- observe_for_information: the observation is expected to settle the question.
- look-1: the chosen observation.
"""

from laix import ActivePerceptionPolicy, DecisionRequest, DecisionClient, iso

decision = DecisionClient(policy=ActivePerceptionPolicy()).decide(
    DecisionRequest(
        subject="late parcel",
        at=iso(),
        attributes={
            "uncertainty": 0.8,
            "observations": [
                {"id": "look-1", "information_gain": 0.7, "cost": 0.1},
                {"id": "look-2", "information_gain": 0.7, "cost": 0.9},
            ],
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
