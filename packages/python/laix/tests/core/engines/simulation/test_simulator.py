"""Planner simulation and comparison."""

from __future__ import annotations

from laix import (
    DecisionProblem,
    MDPPlanner,
    MdpModel,
    MdpTransition,
    Plan,
    Scenario,
    Simulator,
    compare_planners,
    seeded_scenarios,
)


class FixedPlanner:
    def __init__(self, action: str) -> None:
        self.action = action

    def solve(self, problem: DecisionProblem) -> Plan:
        return Plan(
            verb="act",
            confidence=1.0,
            reason_code="fixed",
            rationale=f"always {self.action}",
            action_id=self.action,
        )


def _scenario(horizon: int = 4) -> Scenario:
    def step(state: str, action: str) -> tuple[str, float]:
        return state, 1.0 if action == "right" else 0.0

    return Scenario(
        name="left-or-right",
        simulator=Simulator(step, ("right", "wrong"), start="s", horizon=horizon),
        optimum=float(horizon),
    )


def test_simulator_records_each_step() -> None:
    result = _scenario(2).run(FixedPlanner("right"))

    assert result.total_reward == 2.0
    assert len(result.steps) == 2
    assert result.steps[0].action == "right"


def test_compare_planners_reports_the_best_and_the_gap() -> None:
    report = compare_planners(
        {"right": FixedPlanner("right"), "wrong": FixedPlanner("wrong")},
        [_scenario(4)],
    )
    summary = report.summary()

    assert report.best() == "right"
    assert summary["right"]["mean_reward"] == 4.0
    assert summary["right"]["mean_gap"] == 0.0
    assert summary["wrong"]["mean_gap"] == 1.0


def test_simulator_from_mdp_runs_the_planner() -> None:
    model = MdpModel(
        states=("s0", "s1", "s2"),
        actions=("go", "stay"),
        transitions=(
            MdpTransition("s0", "go", "s1", 1.0, 1.0),
            MdpTransition("s0", "stay", "s0", 1.0, 0.0),
            MdpTransition("s1", "go", "s2", 1.0, 2.0),
            MdpTransition("s1", "stay", "s1", 1.0, 0.0),
        ),
        start="s0",
        discount=0.9,
        horizon=2,
    )
    result = Simulator.from_mdp(model).run(MDPPlanner(model))

    assert result.total_reward == 3.0
    assert [item.action for item in result.steps] == ["go", "go"]


def test_seeded_scenarios_are_repeatable() -> None:
    first = seeded_scenarios(7, count=2, horizon=3)
    second = seeded_scenarios(7, count=2, horizon=3)

    assert [item.name for item in first] == [item.name for item in second]
    assert [item.optimum for item in first] == [item.optimum for item in second]
    report = compare_planners({"a": FixedPlanner("a")}, first)
    assert report.best() == "a"


def test_seeded_mdp_simulation_is_repeatable() -> None:
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
    simulator = Simulator.from_mdp(model, seed=7)
    first = simulator.run(FixedPlanner("go"))
    second = simulator.run(FixedPlanner("go"))

    assert first == second
    assert first.final_state in {"s1", "s2"}
    endings = {
        Simulator.from_mdp(model, seed=seed).run(FixedPlanner("go")).final_state
        for seed in range(1, 20)
    }
    assert endings == {"s1", "s2"}
