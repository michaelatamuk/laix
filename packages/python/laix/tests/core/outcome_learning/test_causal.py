"""Causal attribution over observed outcomes."""

from __future__ import annotations

from laix import CausalLedger


def test_difference_in_means() -> None:
    ledger = CausalLedger()
    ledger.add("d1", arm="ask", outcome=1.0)
    ledger.add("d2", arm="ask", outcome=1.0)
    ledger.add("d3", arm="wait", outcome=0.0)
    ledger.add("d4", arm="wait", outcome=0.0)

    effect = ledger.effect("ask", "wait")
    assert effect.estimate == 1.0
    assert effect.method == "difference-in-means"


def test_inverse_propensity_weighting() -> None:
    ledger = CausalLedger()
    ledger.add("d1", arm="ask", outcome=1.0, propensity=0.5)
    ledger.add("d2", arm="wait", outcome=0.0, propensity=0.5)

    effect = ledger.effect("ask", "wait")
    assert effect.estimate == 2.0
    assert effect.method == "inverse-propensity"


def test_both_arms_are_required() -> None:
    ledger = CausalLedger()
    ledger.add("d1", arm="ask", outcome=1.0)

    try:
        ledger.effect("ask", "wait")
    except ValueError as exc:
        assert "both arms" in str(exc)
    else:
        raise AssertionError("expected ValueError")
