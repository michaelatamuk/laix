"""Causal attribution over observed outcomes."""

from __future__ import annotations

from laix import CausalLedger, Outcome


def test_difference_in_means() -> None:
    ledger = CausalLedger()
    ledger.add("d1", arm="ask", outcome=1.0)
    ledger.add("d2", arm="ask", outcome=1.0)
    ledger.add("d3", arm="wait", outcome=0.0)
    ledger.add("d4", arm="wait", outcome=0.0)

    effect = ledger.effect("ask", "wait")
    assert effect.estimate == 1.0
    assert effect.method == "difference-in-means"
    assert effect.standard_error == 0.0
    assert effect.ci_low == effect.ci_high == 1.0


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


def test_outcomes_feed_the_ledger() -> None:
    outcomes = [
        Outcome(
            id="o1",
            decision_id="d1",
            metric="time",
            before=10.0,
            after=4.0,
            delta=-6.0,
            label="helped",
            direction="lower-better",
        ),
        Outcome(
            id="o2",
            decision_id="d2",
            metric="time",
            before=10.0,
            after=10.0,
            delta=0.0,
            label="neutral",
        ),
    ]
    ledger = CausalLedger.from_outcomes(outcomes, {"d1": "ask", "d2": "wait"})

    assert [item.outcome for item in ledger.records] == [6.0, 0.0]
    assert ledger.effect("ask", "wait").estimate == 6.0


def test_effect_by_context_skips_incomplete_strata() -> None:
    ledger = CausalLedger()
    ledger.add("d1", arm="ask", outcome=1.0, context={"stratum": "east"})
    ledger.add("d2", arm="wait", outcome=0.0, context={"stratum": "east"})
    ledger.add("d3", arm="ask", outcome=1.0, context={"stratum": "west"})

    effects = ledger.effect_by_context("ask", "wait")
    assert sorted(effects) == ["east"]
    assert effects["east"].estimate == 1.0
