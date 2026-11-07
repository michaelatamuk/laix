"""Planner scores across a set of scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from .planner_score import PlannerScore


@dataclass(frozen=True, slots=True)
class SimulationReport:
    """Planner scores across a set of scenarios."""

    rows: tuple[PlannerScore, ...]

    def summary(self) -> dict[str, dict[str, float]]:
        buckets: dict[str, list[PlannerScore]] = {}
        for row in self.rows:
            buckets.setdefault(row.planner, []).append(row)
        return {
            planner: {
                "runs": len(items),
                "mean_reward": round(
                    sum(item.total_reward for item in items) / len(items), 6
                ),
                "mean_gap": round(
                    sum(item.optimality_gap or 0.0 for item in items) / len(items), 6
                ),
            }
            for planner, items in sorted(buckets.items())
        }

    def best(self) -> str | None:
        summary = self.summary()
        if not summary:
            return None
        return sorted(
            summary,
            key=lambda planner: (-summary[planner]["mean_reward"], planner),
        )[0]

    def to_dict(self) -> dict[str, object]:
        return {
            "rows": [row.to_dict() for row in self.rows],
            "summary": self.summary(),
            "best": self.best(),
        }


__all__ = ["SimulationReport"]
