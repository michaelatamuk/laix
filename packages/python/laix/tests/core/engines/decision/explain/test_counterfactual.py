from __future__ import annotations

from laix import Decision, counterfactual_attribution


def _decision() -> Decision:
    return Decision(
        verb="ask",
        confidence=0.8,
        reason_code="value_of_decision",
        rationale="ask balances the terms",
        action_id="ask",
        score=1.0,
        attributes={
            "utility": 0.5,
            "commitment_score": 0.6,
            "execution_score": 0.0,
            "human_attention_score": -0.1,
        },
        alternatives=(
            {
                "action_id": "pay",
                "verb": "act",
                "utility": 0.8,
                "commitment": -0.2,
                "execution": -0.3,
                "human_attention": -0.1,
                "total": 0.2,
            },
            {
                "action_id": "wait",
                "verb": "wait",
                "utility": 0.2,
                "commitment": 0.0,
                "execution": 0.0,
                "human_attention": 0.0,
                "total": 0.2,
            },
        ),
    )


def test_counterfactual_finds_the_smallest_gap() -> None:
    report = counterfactual_attribution(_decision())

    assert report.chosen_id == "ask"
    assert report.minimal is not None
    assert report.minimal.alternative_id == "pay"
    assert 0.8 <= report.minimal.delta <= 0.80001
    assert report.counterfactuals[0].delta <= report.counterfactuals[-1].delta


def test_counterfactual_handles_a_missing_component() -> None:
    decision = Decision(
        verb="ask",
        confidence=0.8,
        reason_code="x",
        rationale="x",
        action_id="ask",
        score=1.0,
        attributes={},
        alternatives=({"action_id": "pay", "total": 0.2},),
    )

    report = counterfactual_attribution(decision)

    assert report.counterfactuals == ()
    assert report.minimal is None
