"""Approval and execution stay inside the host task.

LAIX decides. The host asks a person when the decision needs approval and runs
the action through its own execution bridge.
"""

from laix import ActionOption, Belief, DecisionRequest, Layer, Situation

options = (
    ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
    ActionOption(
        id="approve",
        verb="act",
        name="approve the repair",
        expected_benefit=0.95,
        risk=0.05,
        requires_approval=True,
    ),
)

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="bathroom repair",
        at="2026-11-01T10:00:00+00:00",
        situation=Situation(
            id="repair-1",
            at="2026-11-01T10:00:00+00:00",
            subject="bathroom repair",
            beliefs=(Belief(id="approve", proposition="the repair is ready", confidence=0.95),),
            attributes={"urgency": 0.9},
        ),
        options=options,
        confidence=0.9,
        confidence_source="host-calibrated",
        calibrated=True,
    )
)[0]

chosen = next(option for option in options if option.id == decision.action_id)
layer.bridge().register(chosen.name, lambda action, context: {"done": action.name})
receipt = layer.execute(decision, actor="agent", approver="owner")

print(receipt.status, receipt.action_name, decision.requires_approval)
