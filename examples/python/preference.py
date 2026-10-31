"""Preference is unclear. Ask the question that reduces it most.

The result is:

    ask ask_preference q2

- ask: put one question to the person.
- ask_preference: the answer resolves an unknown preference.
- q2: the question with the best information gain per cost.
"""

from laix import DecisionRequest, Layer, PreferenceElicitationPolicy, iso

decision = Layer(policy=PreferenceElicitationPolicy()).decide(
    DecisionRequest(
        subject="notification style",
        at=iso(),
        attributes={
            "uncertainty": 0.8,
            "questions": [
                {"id": "q1", "information_gain": 0.2, "cost": 1},
                {"id": "q2", "information_gain": 0.8, "cost": 1},
            ],
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
