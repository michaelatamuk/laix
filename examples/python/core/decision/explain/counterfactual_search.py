"""CDA search: find the smallest input change that flips a rule-based decision."""

from __future__ import annotations

from laix import CounterfactualVariable, counterfactual_search

report = counterfactual_search(
    lambda values: "escalate" if values["risk"] >= 0.5 else "act",
    (CounterfactualVariable("risk", 0.4, 0.2, 0.8, step=0.05),),
    max_changes=1,
)

print(report.chosen_id, report.counterfactual_id, report.changes[0].new, report.distance)
