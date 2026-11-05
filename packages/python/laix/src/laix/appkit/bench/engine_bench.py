"""A tiny engine bench: compare planners on the same deterministic chain."""

from __future__ import annotations

from ...core.engines.contract.engine import DecisionProblem, Plan
from ...core.engines.planners.mdp.mdp import MDPEngine, MdpModel, MdpTransition
from ...core.engines.simulation.simulator import Scenario, SimulationReport, Simulator, compare_engines


class FixedActionEngine:
    """A baseline that always chooses one action."""

    def __init__(self, action: str) -> None:
        self.action = action

    def solve(self, problem: DecisionProblem) -> Plan:
        return Plan(
            verb="act",
            confidence=1.0,
            reason_code="fixed_action",
            rationale=f"always choose {self.action}",
            action_id=self.action,
        )


def _chain_model(horizon: int = 4) -> MdpModel:
    states = tuple(f"s{index}" for index in range(horizon + 1))
    transitions = tuple(
        transition
        for index in range(horizon)
        for transition in (
            MdpTransition(f"s{index}", "go", f"s{index + 1}", 1.0, 1.0),
            MdpTransition(f"s{index}", "stay", f"s{index}", 1.0, 0.0),
        )
    )
    return MdpModel(
        states=states,
        actions=("go", "stay"),
        transitions=transitions,
        start="s0",
        discount=0.9,
        horizon=horizon,
    )


def run_engine_bench(horizon: int = 4) -> SimulationReport:
    """Compare the MDP planner with a do-nothing baseline."""
    model = _chain_model(horizon)
    scenario = Scenario(
        name="forward-chain",
        simulator=Simulator.from_mdp(model),
        optimum=float(horizon),
    )
    return compare_engines(
        {
            "mdp": MDPEngine(model),
            "stay-baseline": FixedActionEngine("stay"),
        },
        [scenario],
    )


__all__ = ["FixedActionEngine", "run_engine_bench"]
