"""A budget and three requests. Fund the best value first.

The result is:

    act allocate ['a', 'b']

- act: commit the allocation.
- allocate: the policy funds a portfolio.
- ['a', 'b']: the requests that fit the budget, best value per cost first.
"""

from laix import AllocationPolicy, DecisionRequest, Layer, iso

decision = Layer(policy=AllocationPolicy()).decide(
    DecisionRequest(
        subject="weekly work",
        at=iso(),
        attributes={
            "budget": 10,
            "requests": [
                {"id": "a", "value": 6, "cost": 4},
                {"id": "b", "value": 5, "cost": 6},
                {"id": "c", "value": 9, "cost": 20},
            ],
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.intent.args["ids"])
