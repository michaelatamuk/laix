"""Choose an option with the expected-utility engine."""

from __future__ import annotations

from laix import (
    ActionOption,
    DecisionRequest,
    EnginePolicy,
    UtilityEngine,
    decide,
)

policy = EnginePolicy(UtilityEngine(), name="utility.v1")
decision = decide(
    DecisionRequest(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
            ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
        ),
    ),
    policy=policy,
)[0]
print(decision.verb, decision.action_id, decision.score)
