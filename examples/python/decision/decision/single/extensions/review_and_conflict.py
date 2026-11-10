"""Reuse a past decision, then resolve a goal conflict."""

from __future__ import annotations

from laix import (
    ActionOption,
    CaseBasedPlanner,
    ConflictResolutionPlanner,
    PastDecision,
    PlannerInput,
)

case_plan = CaseBasedPlanner(
    (PastDecision(subject="send the report", action_id="send-now"),)
).solve(
    PlannerInput(
        subject="send the report today",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="send-now", verb="act", name="send now"),
            ActionOption(id="send-later", verb="wait", name="send later"),
        ),
    )
)
conflict_plan = ConflictResolutionPlanner().solve(
    PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(ActionOption(id="a", verb="act", name="a"),),
        attributes={
            "goal_conflicts": [
                {"id": "g1", "left": "speed", "right": "safety", "severity": 0.9}
            ]
        },
    )
)

print("case", case_plan.action_id, case_plan.reason_code)
print("conflict", conflict_plan.verb, conflict_plan.reason_code)
