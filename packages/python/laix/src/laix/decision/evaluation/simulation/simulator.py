"""Run planners in a model, and compare them on the same scenarios.

The simulator is intentionally small: the host supplies a deterministic step
function and the planner chooses an action for the current state. That is enough
to compare a rule policy, a utility planner and an MDP planner on one trace.
"""

from __future__ import annotations

import random
from typing import Callable, Iterable, Mapping, Sequence

from ...support.time import iso
from ...contract.planner import Planner
from ...contract.planner_input import PlannerInput
from .planner_benchmark_row import PlannerBenchmarkRow
from ...planners.single.mdp.mdp_model import MdpModel
from .scenario import Scenario
from .simulation_report import SimulationReport
from .simulation_result import SimulationResult
from .simulation_step import SimulationStep

Step = Callable[[str, str], tuple[str, float]]
RandomStep = Callable[[str, str, random.Random], tuple[str, float]]


class Simulator:
    """A deterministic environment a planner can be run in."""

    def __init__(
        self,
        step: Step,
        actions: Sequence[str],
        *,
        start: str,
        horizon: int = 10,
        name: str = "scenario",
        random_step: RandomStep | None = None,
        seed: int | None = None,
    ) -> None:
        if not actions:
            raise ValueError("a simulator needs at least one action")
        if horizon < 0:
            raise ValueError("horizon must not be negative")
        self.step = step
        self.actions = tuple(actions)
        self.start = start
        self.horizon = horizon
        self.name = name
        self.random_step = random_step
        self.seed = seed

    def run(self, planner: Planner) -> SimulationResult:
        state = self.start
        steps: list[SimulationStep] = []
        total = 0.0
        rng = (
            random.Random(self.seed)
            if self.random_step is not None and self.seed is not None
            else None
        )
        for index in range(self.horizon):
            problem = PlannerInput(
                subject=self.name,
                at=iso(),
                attributes={"state": state},
            )
            plan = planner.solve(problem)
            action = plan.action_id
            if action is None or action not in self.actions:
                steps.append(
                    SimulationStep(
                        step=index,
                        state=state,
                        action=action,
                        reward=0.0,
                        next_state=state,
                    )
                )
                break
            if self.random_step is not None and rng is not None:
                next_state, reward = self.random_step(state, action, rng)
            else:
                next_state, reward = self.step(state, action)
            steps.append(
                SimulationStep(
                    step=index,
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                )
            )
            total += reward
            state = next_state
        return SimulationResult(
            scenario=self.name,
            steps=tuple(steps),
            total_reward=round(total, 6),
            final_state=state,
        )

    @classmethod
    def from_mdp(
        cls,
        model: MdpModel,
        *,
        start: str | None = None,
        seed: int | None = None,
    ) -> "Simulator":
        """Build a simulator from an MDP.

        Without ``seed`` the run follows the most likely transition and is
        repeatable. With ``seed`` it samples transitions, and each run resets
        the generator so the same seed gives the same trace.
        """
        resolved_start = start or model.start
        horizon = 10 if model.horizon is None else model.horizon

        def step(state: str, action: str) -> tuple[str, float]:
            rows = model.outgoing(state, action)
            if not rows:
                return state, 0.0
            chosen = sorted(rows, key=lambda item: (-item.probability, item.next_state))[0]
            return chosen.next_state, chosen.reward

        def random_step(
            state: str,
            action: str,
            rng: random.Random,
        ) -> tuple[str, float]:
            rows = model.outgoing(state, action)
            if not rows:
                return state, 0.0
            roll = rng.random()
            cumulative = 0.0
            for item in rows:
                cumulative += item.probability
                if roll <= cumulative:
                    return item.next_state, item.reward
            return rows[-1].next_state, rows[-1].reward

        return cls(
            step,
            model.actions,
            start=resolved_start,
            horizon=horizon,
            name=f"mdp:{model.start}",
            random_step=random_step if seed is not None else None,
            seed=seed,
        )


def compare_planners(
    planners: Mapping[str, Planner],
    scenarios: Iterable[Scenario],
) -> SimulationReport:
    """Run every planner on every scenario and report reward and optimality gap."""
    rows: list[PlannerBenchmarkRow] = []
    for scenario in scenarios:
        for name, planner in planners.items():
            result = scenario.run(planner)
            gap = None
            if scenario.optimum is not None:
                gap = round(
                    max(
                        0.0,
                        (scenario.optimum - result.total_reward)
                        / max(abs(scenario.optimum), 1e-9),
                    ),
                    6,
                )
            rows.append(
                PlannerBenchmarkRow(
                    planner=name,
                    scenario=scenario.name,
                    total_reward=result.total_reward,
                    steps=len(result.steps),
                    optimality_gap=gap,
                )
            )
    return SimulationReport(rows=tuple(rows))


def seeded_scenarios(
    seed: int,
    *,
    count: int = 3,
    horizon: int = 8,
    actions: Sequence[str] = ("a", "b"),
) -> tuple[Scenario, ...]:
    """Build deterministic scenarios with a known optimum.

    Each scenario is a finite chain of states. The reward table comes from the
    seed; the optimum is computed by backward induction.
    """
    if count < 1:
        raise ValueError("count must be at least one")
    if horizon < 1:
        raise ValueError("horizon must be at least one")
    rng = random.Random(seed)
    scenarios: list[Scenario] = []
    for index in range(count):
        table: dict[str, dict[str, float]] = {}
        for step_index in range(horizon):
            state = f"s{step_index}"
            table[state] = {
                action: round(rng.uniform(-1.0, 1.0), 6) for action in actions
            }

        def make_step(values: dict[str, dict[str, float]]) -> Step:
            def step(state: str, action: str) -> tuple[str, float]:
                reward = values.get(state, {}).get(action, 0.0)
                index = int(state[1:]) if state.startswith("s") else 0
                return f"s{index + 1}", reward

            return step

        simulator = Simulator(
            make_step(table),
            actions,
            start="s0",
            horizon=horizon,
            name=f"seeded-{seed}-{index}",
        )
        best = 0.0
        for step_index in range(horizon):
            state = f"s{step_index}"
            best += max(table.get(state, {}).values(), default=0.0)
        scenarios.append(
            Scenario(
                name=f"seeded-{seed}-{index}",
                simulator=simulator,
                optimum=round(best, 6),
            )
        )
    return tuple(scenarios)


__all__ = [
    "PlannerBenchmarkRow",
    "Scenario",
    "SimulationReport",
    "SimulationResult",
    "SimulationStep",
    "Simulator",
    "compare_planners",
    "seeded_scenarios",
]
