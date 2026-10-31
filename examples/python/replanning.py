"""The old plan broke. Pick a replacement that still fits the limits.

The result is:

    act replan plan-fast

- act: adopt a new plan.
- replan: the old plan is replaced.
- plan-fast: the feasible plan with the best success against cost.
"""

from laix import DecisionRequest, Layer, ReplanningPolicy, iso

decision = Layer(policy=ReplanningPolicy()).decide(
    DecisionRequest(
        subject="delivery route",
        at=iso(),
        attributes={
            "min_success": 0.7,
            "max_cost": 5,
            "plans": [
                {"id": "plan-slow", "success_probability": 0.95, "cost": 10, "deadline_risk": 0.1},
                {"id": "plan-fast", "success_probability": 0.8, "cost": 1, "deadline_risk": 0.1},
            ],
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
