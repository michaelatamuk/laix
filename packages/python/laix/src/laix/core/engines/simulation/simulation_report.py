"""Engine scores across a set of scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from .engine_score import EngineScore


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

    def to_dict(self) -> dict[str, object]:
        return {
            "rows": [row.to_dict() for row in self.rows],
            "summary": self.summary(),
            "best": self.best(),
        }


__all__ = ["SimulationReport"]
