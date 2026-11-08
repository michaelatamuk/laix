"""An offer below the reservation. Counter instead of accepting.

The result is:

    act counter_offer 12.5

- act: respond to the offer.
- counter_offer: the offer is too low, so name a better number.
- 12.5: halfway between the offer and the target, never below the reservation.
"""

from laix import DecisionRequest, DecisionClient, NegotiationPolicy, iso

decision = DecisionClient(policy=NegotiationPolicy()).decide(
    DecisionRequest(
        subject="contract renewal",
        at=iso(),
        attributes={
            "offer": 5,
            "reservation": 10,
            "target": 20,
            "round": 1,
            "max_rounds": 5,
        },
    )
)[0]

print(decision.verb, decision.reason_code, decision.intent.args["amount"])
