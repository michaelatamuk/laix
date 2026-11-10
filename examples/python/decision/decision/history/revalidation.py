"""Decide whether an earlier decision still holds."""

from __future__ import annotations

from laix import ActionOption, PlannerInput, RevalidationPlanner, UtilityPlanner

planner = RevalidationPlanner(UtilityPlanner())


def decide(previous: str):
    return planner.solve(
        PlannerInput(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            options=(
                ActionOption(id="timid", verb="act", name="timid", expected_benefit=0.6),
                ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9),
            ),
            attributes={"previous_action_id": previous},
        )
    )


held = decide("bold")
revised = decide("timid")

print(held.reason_code, revised.reason_code, revised.action_id)
