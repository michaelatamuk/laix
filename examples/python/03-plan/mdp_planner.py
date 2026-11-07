"""Plan one step in a finite MDP."""

from __future__ import annotations

from laix import (
    DecisionRequest,
    EnginePolicy,
    MdpModel,
    MDPPlanner,
    MdpTransition,
    decide,
)

model = MdpModel(
    states=("s0", "s1"),
    actions=("go", "stay"),
    transitions=(
        MdpTransition("s0", "go", "s1", 1.0, 1.0),
        MdpTransition("s0", "stay", "s0", 1.0, 0.0),
        MdpTransition("s1", "go", "s1", 1.0, 2.0),
    ),
    start="s0",
    discount=0.9,
    horizon=2,
)
decision = decide(
    DecisionRequest(subject="choose", at="2026-11-01T10:00:00+00:00"),
    policy=EnginePolicy(MDPPlanner(model), name="mdp.v1"),
)[0]
print(decision.verb, decision.action_id, decision.score)
