"""Plan under a belief in a small POMDP."""

from __future__ import annotations

from laix import (
    DecisionProblem,
    ObservationProbability,
    POMDPEngine,
    PomdpModel,
    PomdpTransition,
    belief_from_state,
)

model = PomdpModel(
    states=("s0", "s1"),
    actions=("go", "stay"),
    observations=("o0", "o1"),
    transitions=(
        PomdpTransition("s0", "go", "s1", 1.0, 1.0),
        PomdpTransition("s0", "stay", "s0", 1.0, 0.0),
        PomdpTransition("s1", "go", "s1", 1.0, 2.0),
        PomdpTransition("s1", "stay", "s1", 1.0, 0.0),
    ),
    observation_table=(
        ObservationProbability("s0", "go", "o0", 1.0),
        ObservationProbability("s0", "stay", "o0", 1.0),
        ObservationProbability("s1", "go", "o1", 1.0),
        ObservationProbability("s1", "stay", "o1", 1.0),
    ),
    discount=0.9,
    horizon=2,
)
plan = POMDPEngine(model).solve(
    DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        attributes={"belief": belief_from_state("s0", model.states)},
    )
)
print(plan.verb, plan.action_id, plan.score)
