"""The kitchen sink is about to overflow. What should the app do?

The result is:

    act policy_rule option-close-valve

That means:

- act: do something now.
- policy_rule: a written policy rule made the choice.
- option-close-valve: the chosen action is to close the valve.

The belief says the sink is about to overflow with 95% confidence. Urgency is
0.9. Closing the valve has high benefit and low risk, so the rule chooses it.
"""

from laix import ActionOption, Belief, DecisionRequest, DecisionClient, Situation, iso

layer = DecisionClient()
decision = layer.decide(
    DecisionRequest(
        subject="kitchen sink",
        at=iso(),
        situation=Situation(
            id="sink-1",
            at=iso(),
            subject="kitchen sink",
            beliefs=(
                Belief(
                    id="overflow",
                    proposition="the sink is about to overflow",
                    confidence=0.95,
                ),
            ),
            attributes={"urgency": 0.9},
        ),
        options=(
            ActionOption(id="option-wait", verb="wait", name="keep-watching", expected_benefit=0.1),
            ActionOption(
                id="option-close-valve",
                verb="act",
                name="close the valve",
                expected_benefit=0.95,
                risk=0.05,
                reversible=True,
            ),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
