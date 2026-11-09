"""CA-VOD with a small belief-state model: value the future, not only now."""

from __future__ import annotations

from laix import (
    ActionOption,
    CAVODPlanner,
    ObservationProbability,
    PlannerInput,
    PomdpModel,
    PomdpTransition,
)

model = PomdpModel(
    states=("safe", "risky"),
    actions=("act", "ask", "wait"),
    observations=("ok", "good", "bad"),
    transitions=(
        PomdpTransition(state="safe", action="act", next_state="safe", reward=1.0),
        PomdpTransition(state="risky", action="act", next_state="risky", reward=-1.0),
        PomdpTransition(state="safe", action="ask", next_state="safe"),
        PomdpTransition(state="risky", action="ask", next_state="risky"),
        PomdpTransition(state="safe", action="wait", next_state="safe"),
        PomdpTransition(state="risky", action="wait", next_state="risky"),
    ),
    observation_table=(
        ObservationProbability(next_state="safe", action="act", observation="ok"),
        ObservationProbability(next_state="risky", action="act", observation="ok"),
        ObservationProbability(next_state="safe", action="ask", observation="good"),
        ObservationProbability(next_state="risky", action="ask", observation="bad"),
        ObservationProbability(next_state="safe", action="wait", observation="ok"),
        ObservationProbability(next_state="risky", action="wait", observation="ok"),
    ),
    discount=0.9,
    horizon=2,
)

plan = CAVODPlanner(
    pomdp_model=model,
    belief={"safe": 0.5, "risky": 0.5},
).solve(
    PlannerInput(
        subject="belief",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.55),
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.2),
            ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
        ),
        attributes={},
    )
)

print(plan.action_id, plan.attributes["future_value"], plan.attributes["horizon"])
