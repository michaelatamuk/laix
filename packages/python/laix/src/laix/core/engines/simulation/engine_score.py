"""One engine's result on one scenario."""

from __future__ import annotations

from dataclasses import dataclass


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


__all__ = ["EngineScore"]
