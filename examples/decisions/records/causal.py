"""Estimate a treatment effect from observed outcomes."""

from __future__ import annotations

from laix import CausalLedger

ledger = CausalLedger()
ledger.add("d1", arm="ask", outcome=1.0)
ledger.add("d2", arm="ask", outcome=1.0)
ledger.add("d3", arm="wait", outcome=0.0)
ledger.add("d4", arm="wait", outcome=0.0)

effect = ledger.effect("ask", "wait")
print(effect.estimate, effect.method)
