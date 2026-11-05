"""One named simulator, with an optional known optimum."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .decision_engine import DecisionEngine
from .simulation_result import SimulationResult

if TYPE_CHECKING:
    from .simulator import Simulator


@dataclass(frozen=True, slots=True)
class Scenario:
    """One named simulator, with an optional known optimum."""

    name: str
    simulator: "Simulator"
    optimum: float | None = None

    def run(self, engine: DecisionEngine) -> SimulationResult:
        result = self.simulator.run(engine)
        return SimulationResult(
            scenario=self.name,
            steps=result.steps,
            total_reward=result.total_reward,
            final_state=result.final_state,
        )


__all__ = ["Scenario"]
