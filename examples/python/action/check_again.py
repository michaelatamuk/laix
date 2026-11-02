"""A parcel is running late. Check the tracking page before asking anyone.

The result is:

    observe policy_rule option-check-tracking

That means:

- observe: get more information yourself before deciding.
- policy_rule: a written policy rule made the choice.
- option-check-tracking: the chosen action is to read the tracking page.

The parcel looks late, but a cheap check can settle it. The rule prefers that
check before asking the courier.
"""

from laix import ActionOption, Belief, DecisionRequest, Layer, Situation, iso

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="late parcel",
        at=iso(),
        situation=Situation(
            id="parcel-1",
            at=iso(),
            subject="late parcel",
            beliefs=(
                Belief(
                    id="late",
                    proposition="the parcel is late",
                    confidence=0.6,
                ),
            ),
            attributes={"urgency": 0.8, "needs_more_info": True},
        ),
        options=(
            ActionOption(id="option-wait", verb="wait", name="keep waiting", expected_benefit=0.2),
            ActionOption(id="option-check-tracking", verb="observe", name="read the tracking page", expected_benefit=0.6),
            ActionOption(id="option-ask-courier", verb="ask", name="ask the courier", expected_benefit=0.4),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
