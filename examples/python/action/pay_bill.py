"""A payment is due today, and a person must approve it.

The result is:

    act policy_rule option-pay True

That means:

- act: the policy chooses to pay now.
- policy_rule: a written policy rule made the choice.
- option-pay: the chosen action is the payment.
- True: a person must approve before the payment runs.

The layer makes the choice; the application asks for approval because the
chosen action requires it.
"""

from laix import Action, Belief, DecisionRequest, Layer, Situation, iso

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="electricity bill payment",
        at=iso(),
        situation=Situation(
            id="payment-1",
            at=iso(),
            subject="electricity bill payment",
            beliefs=(
                Belief(
                    id="due",
                    proposition="the bill is due today",
                    confidence=0.95,
                ),
            ),
            attributes={"urgency": 0.9},
        ),
        options=(
            Action(id="option-wait", verb="wait", name="pay later", expected_benefit=0.1),
            Action(
                id="option-pay",
                verb="act",
                name="pay the bill",
                expected_benefit=0.9,
                requires_approval=True,
            ),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id, decision.requires_approval)
