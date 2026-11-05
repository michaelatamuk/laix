"""An urgent alert chooses an action; the chosen assignment needs approval."""

from __future__ import annotations

from laix import ActionOption, Belief, DecisionRequest, Layer, Situation, iso

decision = Layer().decide(
    DecisionRequest(
        subject="monitored area alert",
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
            ActionOption(id="wait", verb="wait", name="keep watching", expected_benefit=0.2),
            ActionOption(
                id="request-check",
                verb="ask",
                name="request a better view",
                expected_benefit=0.6,
            ),
            ActionOption(
                id="assign-owner",
                verb="act",
                name="assign an owner",
                expected_benefit=0.9,
                requires_approval=True,
            ),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id, decision.requires_approval)
