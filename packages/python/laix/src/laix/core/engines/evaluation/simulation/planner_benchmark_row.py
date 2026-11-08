"""One planner's result on one scenario."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlannerBenchmarkRow:
    """One planner's result on one scenario."""

    planner: str
    scenario: str
    total_reward: float
    steps: int
    optimality_gap: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "planner": self.planner,
            "scenario": self.scenario,
            "total_reward": round(self.total_reward, 6),
            "steps": self.steps,
            "optimality_gap": self.optimality_gap,
        }


__all__ = ["PlannerBenchmarkRow"]
