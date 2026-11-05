"""Show utility constraints, stochastic simulation and POMDP comparison."""

from __future__ import annotations

from laix import (
    ActionOption,
    Constraint,
    DecisionProblem,
    MdpModel,
    MdpTransition,
    ObservationProbability,
    POMDPEngine,
    Plan,
    PomdpModel,
    PomdpTransition,
    Situation,
    Simulator,
    UtilityEngine,
    belief_from_state,
    compare_pomdp_to_mdp,
)


class AlwaysGo:
    def solve(self, problem: DecisionProblem) -> Plan:
        return Plan(
            verb="act",
            confidence=1.0,
            reason_code="fixed",
            rationale="always go",
            action_id="go",
        )


# 1. UtilityEngine enforces a hard Situation risk constraint.
situation = Situation(
    id="sit-1",
    at="2026-11-01T10:00:00+00:00",
    subject="leak",
    constraints=(Constraint(id="risk-limit", kind="risk", value=0.2),),
)
utility = UtilityEngine().solve(
    DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=(
            ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
            ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
        ),
    )
)
print(utility.action_id, utility.alternatives[0]["rejected_because"])

# 2. A seeded stochastic simulator gives a repeatable rollout.
model = MdpModel(
    states=("s0", "s1", "s2"),
    actions=("go",),
    transitions=(
        MdpTransition("s0", "go", "s1", 0.5, 1.0),
        MdpTransition("s0", "go", "s2", 0.5, 2.0),
    ),
    start="s0",
    horizon=1,
)
result = Simulator.from_mdp(model, seed=7).run(AlwaysGo())
print(result.final_state, result.total_reward)

# 3. A POMDP belief is compared with the MDP value of the likely state.
pomdp = PomdpModel(
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
    horizon=1,
)
mdp = MdpModel(
    states=("s0", "s1"),
    actions=("go", "stay"),
    transitions=(
        MdpTransition("s0", "go", "s1", 1.0, 1.0),
        MdpTransition("s0", "stay", "s0", 1.0, 0.0),
        MdpTransition("s1", "go", "s1", 1.0, 2.0),
        MdpTransition("s1", "stay", "s1", 1.0, 0.0),
    ),
    start="s0",
    discount=0.9,
    horizon=1,
)
comparison = compare_pomdp_to_mdp(
    pomdp,
    mdp,
    belief_from_state("s0", pomdp.states),
    horizon=1,
)
plan = POMDPEngine(pomdp).solve(
    DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        attributes={"belief": belief_from_state("s0", pomdp.states)},
    )
)
print(comparison.state, comparison.gap, plan.action_id)
