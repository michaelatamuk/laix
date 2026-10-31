"""GeoResponse — a change alert calls LAIX to choose the next action.

GeoResponse keeps its alert store, imagery and analyst roster. It maps an open
alert to a Situation and gives LAIX the actions it can afford.

The result is:

    act policy_rule assign-owner True

- act: assign the alert now.
- policy_rule: a written policy rule made the choice.
- assign-owner: the chosen action.
- True: a person approves the assignment before it runs.
"""

from laix import Action, Belief, DecisionRequest, Layer, Situation, iso

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="GeoResponse change alert",
        at=iso(),
        situation=Situation(
            id="alert-1",
            at=iso(),
            subject="new construction in a monitored area",
            beliefs=(
                Belief(
                    id="change",
                    proposition="the change is real",
                    confidence=0.92,
                ),
            ),
            attributes={"urgency": 0.9},
        ),
        options=(
            Action(id="wait", verb="wait", name="keep watching", expected_benefit=0.2),
            Action(id="request-check", verb="ask", name="request a better view", expected_benefit=0.6),
            Action(
                id="assign-owner",
                verb="act",
                name="assign an analyst",
                expected_benefit=0.9,
                requires_approval=True,
            ),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id, decision.requires_approval)
