"""The full live loop: stream, decision, execution, outcome, calibration and timeline."""

from __future__ import annotations

from datetime import datetime, timezone

from laix import (
    ActionOption,
    AttentionBudget,
    Commitment,
    DecisionCalibrationSample,
    DecisionRequest,
    DecisionTimeline,
    EnginePolicy,
    ExecutionBridge,
    LiveDecisionEngine,
    ManualClock,
    Outcome,
    StreamSession,
    calibrate_decision,
    decision_calibration_report,
)

commitments = (
    Commitment(
        id="c1",
        subject="send the report",
        due="2026-11-01T09:00:00+00:00",
    ),
)
budget = AttentionBudget(total=1.0)
timeline = DecisionTimeline()
policy = EnginePolicy(LiveDecisionEngine(), name="live.v1")
session = StreamSession(
    policy.decide,
    stream_id="DESK",
    capacity=4,
    timeline=timeline,
    attention_budget=budget,
    clock=ManualClock(datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)),
)

request = DecisionRequest(
    subject="live loop",
    at="2026-11-01T10:00:00+00:00",
    options=(
        ActionOption(
            id="fast",
            verb="act",
            name="fast",
            expected_benefit=1.0,
            reversible=False,
            interrupt_cost=0.6,
            params={"commitments": {"violates": ["c1"]}},
        ),
        ActionOption(
            id="safe",
            verb="act",
            name="safe",
            expected_benefit=0.6,
            interrupt_cost=0.2,
            params={"commitments": {"fulfills": ["c1"]}},
        ),
    ),
    attributes={"commitments": commitments, "attention_budget": budget},
)

decision = session.observe(request)[0]
action = next(option for option in request.options if option.id == decision.action_id)
bridge = ExecutionBridge(handlers={action.name: lambda call, context: {"done": True}})
receipt = bridge.execute(decision, action=action, actor="agent")
outcome = Outcome(
    id="o1",
    decision_id=decision.decision_id,
    metric="resolved",
    before=0.0,
    after=1.0,
    delta=1.0,
    label="helped",
)
report = decision_calibration_report(
    [
        DecisionCalibrationSample(
            confidence=decision.confidence,
            correct=True,
            verb=decision.verb,
            action_id=decision.action_id or "",
        )
    ]
)
calibrated = calibrate_decision(decision, report)

print(
    decision.action_id,
    decision.verb,
    receipt.status,
    outcome.label,
    timeline.report().decisions,
    round(budget.remaining(), 1),
    calibrated.confidence,
)
