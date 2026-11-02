"""RootCause — a quality reading calls LAIX to choose the next action.

RootCause keeps the line, case, baseline and report. It maps one reading to a
Situation and gives LAIX the actions the quality team can take.

The result is:

    guide policy_rule open-watch

- guide: open a watch for the engineer; the engineer chooses when to look.
- policy_rule: a written policy rule made the choice.
- open-watch: the chosen action.
"""

from laix import ActionOption, Belief, DecisionRequest, Layer, Situation, iso

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="RootCause quality reading",
        at=iso(),
        situation=Situation(
            id="reading-1",
            at=iso(),
            subject="line-6 hydrogen reading",
            beliefs=(
                Belief(
                    id="deviation",
                    proposition="the reading is a real deviation",
                    confidence=0.8,
                ),
            ),
            attributes={
                "urgency": 0.6,
                "line_id": "line-6",
                "parameter": "hydrogen",
                "z": 2.0,
            },
        ),
        options=(
            ActionOption(id="wait", verb="wait", name="keep observing", expected_benefit=0.2),
            ActionOption(id="open-watch", verb="guide", name="open a watch", expected_benefit=0.6),
            ActionOption(id="notify-engineer", verb="act", name="notify the engineer", expected_benefit=0.9),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
