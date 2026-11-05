"""What one engine did in one scenario."""

from __future__ import annotations

from dataclasses import dataclass

from .simulation_step import SimulationStep


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


__all__ = ["SimulationResult"]
