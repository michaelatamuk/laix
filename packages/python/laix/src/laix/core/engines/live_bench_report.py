"""All rows and all per-planner metrics for one benchmark run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .live_bench_row import LiveBenchRow
from .planner_metrics import PlannerMetrics


@dataclass(frozen=True, slots=True)
class LiveBenchReport:
    """All rows and all per-planner metrics for one run."""

    rows: tuple[LiveBenchRow, ...]
    metrics: tuple[PlannerMetrics, ...]
    cases: tuple[str, ...]
    planners: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cases": list(self.cases),
            "planners": list(self.planners),
            "rows": [row.to_dict() for row in self.rows],
            "metrics": [item.to_dict() for item in self.metrics],
        }

    def summary(self) -> str:
        lines = [
            "planner      accuracy  safe  irreversible  mean_ms  mean_score",
            "-----------  --------  ----  ------------  -------  ----------",
        ]
        for item in sorted(
            self.metrics, key=lambda metric: (-metric.accuracy, metric.planner)
        ):
            mean_score = "-" if item.mean_score is None else f"{item.mean_score:.3f}"
            lines.append(
                f"{item.planner:<11}  {item.accuracy:>8.2%}  "
                f"{item.safety_violations:>4}  {item.irreversible:>12}  "
                f"{item.mean_latency_ms:>7.3f}  {mean_score:>10}"
            )
        return "\n".join(lines)


__all__ = ["LiveBenchReport"]
