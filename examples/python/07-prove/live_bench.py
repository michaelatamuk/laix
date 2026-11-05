"""Compare training-free planners on the live decision benchmark."""

from __future__ import annotations

from laix import run_live_bench

report = run_live_bench()
for name in ("utility", "commitment", "execution", "attention"):
    metric = next(item for item in report.metrics if item.planner == name)
    print(name, f"{metric.accuracy:.2f}", metric.safety_violations)
