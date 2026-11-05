"""Build a causal ledger from measured outcomes."""

from __future__ import annotations

from laix import CausalLedger, Outcome

outcomes = (
    Outcome(
        id="o1",
        decision_id="d1",
        metric="time_to_resolve",
        before=10.0,
        after=4.0,
        delta=-6.0,
        label="helped",
        direction="lower-better",
    ),
    Outcome(
        id="o2",
        decision_id="d2",
        metric="time_to_resolve",
        before=10.0,
        after=10.0,
        delta=0.0,
        label="neutral",
    ),
)
ledger = CausalLedger.from_outcomes(outcomes, {"d1": "act", "d2": "wait"})
effect = ledger.effect("act", "wait")
print(effect.estimate, effect.ci_low, effect.ci_high)
