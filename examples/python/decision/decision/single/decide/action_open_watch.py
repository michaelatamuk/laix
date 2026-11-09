"""A quality reading chooses a guide action instead of immediate action."""

from __future__ import annotations

from laix import ActionOption, Belief, DecisionRequest, DecisionClient, Situation, iso

decision = DecisionClient().decide(
    DecisionRequest(
        subject="quality reading",
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
            ActionOption(
                id="notify-engineer",
                verb="act",
                name="notify the engineer",
                expected_benefit=0.9,
            ),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id)
