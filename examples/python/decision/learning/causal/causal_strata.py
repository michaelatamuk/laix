"""Estimate a causal effect with intervals and per-context strata."""

from __future__ import annotations

from laix import CausalLedger

ledger = CausalLedger()
for decision_id, arm, outcome, stratum in (
    ("e1", "ask", 1.0, "east"),
    ("e2", "ask", 3.0, "east"),
    ("e3", "wait", 0.0, "east"),
    ("e4", "wait", 2.0, "east"),
    ("w1", "ask", 2.0, "west"),
    ("w2", "wait", 1.0, "west"),
):
    ledger.add(decision_id, arm=arm, outcome=outcome, context={"stratum": stratum})

overall = ledger.effect("ask", "wait")
east = ledger.effect_by_context("ask", "wait")["east"]
print(
    overall.estimate,
    east.ci_low,
    east.ci_high,
    sorted(ledger.effect_by_context("ask", "wait")),
)
