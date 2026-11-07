"""Compare the MDP planner with a do-nothing baseline."""

from __future__ import annotations

from laix.appkit.bench import run_planner_bench

report = run_planner_bench()
summary = report.summary()
print(
    report.best(),
    summary["mdp"]["mean_reward"],
    summary["stay-baseline"]["mean_gap"],
)
