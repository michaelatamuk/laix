"""Run engines in a model, and compare them on the same scenarios.

The simulator is intentionally small: the host supplies a deterministic step
function and the engine chooses an action for the current state. That is enough
to compare a rule policy, a utility engine and an MDP planner on one trace.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

from ..support.time import iso
from .engine import DecisionEngine, DecisionProblem
from .mdp import MdpModel

Step = Callable[[str, str], tuple[str, float]]


@dataclass(frozen=True, slots=True)
class SimulationStep:
    """One step in a simulated trace."""

    step: int
    state: str
    action: str | None
    reward: float
    next_state: str


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """What one engine did in one scenario."""

    scenario: str
    steps: tuple[SimulationStep, ...]
    total_reward: float
    final_state: str

    def summary(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "steps": len(self.steps),
            "total_reward": round(self.total_reward, 6),
            "final_state": self.final_state,
        }


class Simulator:
    """A deterministic environment an engine can be run in."""

    def __init__(
        self,
        step: Step,
        actions: Sequence[str],
        *,
        start: str,
        horizon: int = 10,
        name: str = "scenario",
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

    def run(self, engine: DecisionEngine) -> SimulationResult:
        state = self.start
        steps: list[SimulationStep] = []
        total = 0.0
        for index in range(self.horizon):
            problem = DecisionProblem(
                subject=self.name,
                at=iso(),
                attributes={"state": state},
            )
            plan = engine.solve(problem)
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
    def from_mdp(cls, model: MdpModel, *, start: str | None = None) -> "Simulator":
        """Build a repeatable simulator from an MDP's most likely transitions."""

        def step(state: str, action: str) -> tuple[str, float]:
            rows = model.outgoing(state, action)
            if not rows:
                return state, 0.0
            chosen = sorted(rows, key=lambda item: (-item.probability, item.next_state))[0]
            return chosen.next_state, chosen.reward

        return cls(
            step,
            model.actions,
            start=start or model.start,
            horizon=10 if model.horizon is None else model.horizon,
            name=f"mdp:{model.start}",
        )


@dataclass(frozen=True, slots=True)
class Scenario:
    """One named simulator, with an optional known optimum."""

    name: str
    simulator: Simulator
    optimum: float | None = None

    def run(self, engine: DecisionEngine) -> SimulationResult:
        result = self.simulator.run(engine)
        return SimulationResult(
            scenario=self.name,
            steps=result.steps,
            total_reward=result.total_reward,
            final_state=result.final_state,
        )


@dataclass(frozen=True, slots=True)
class EngineScore:
    """One engine's result on one scenario."""

    engine: str
    scenario: str
    total_reward: float
    steps: int
    optimality_gap: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "scenario": self.scenario,
            "total_reward": round(self.total_reward, 6),
            "steps": self.steps,
            "optimality_gap": self.optimality_gap,
        }


@dataclass(frozen=True, slots=True)
class SimulationReport:
    """Engine scores across a set of scenarios."""

    rows: tuple[EngineScore, ...]

    def summary(self) -> dict[str, dict[str, float]]:
        buckets: dict[str, list[EngineScore]] = {}
        for row in self.rows:
            buckets.setdefault(row.engine, []).append(row)
        return {
            engine: {
                "runs": len(items),
                "mean_reward": round(
                    sum(item.total_reward for item in items) / len(items), 6
                ),
                "mean_gap": round(
                    sum(item.optimality_gap or 0.0 for item in items) / len(items), 6
                ),
            }
            for engine, items in sorted(buckets.items())
        }

    def best(self) -> str | None:
        summary = self.summary()
        if not summary:
            return None
        return sorted(
            summary,
            key=lambda engine: (-summary[engine]["mean_reward"], engine),
        )[0]


def compare_engines(
    engines: Mapping[str, DecisionEngine],
    scenarios: Iterable[Scenario],
) -> SimulationReport:
    """Run every engine on every scenario and report reward and optimality gap."""
    rows: list[EngineScore] = []
    for scenario in scenarios:
        for name, engine in engines.items():
            result = scenario.run(engine)
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
                EngineScore(
                    engine=name,
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
    "EngineScore",
    "Scenario",
    "SimulationReport",
    "SimulationResult",
    "SimulationStep",
    "Simulator",
    "compare_engines",
    "seeded_scenarios",
]
