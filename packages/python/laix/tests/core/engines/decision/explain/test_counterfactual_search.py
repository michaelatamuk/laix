from __future__ import annotations

from laix import CounterfactualVariable, counterfactual_search


def test_search_finds_a_rule_threshold() -> None:
    report = counterfactual_search(
        lambda values: "escalate" if values["risk"] >= 0.5 else "act",
        (CounterfactualVariable("risk", 0.4, 0.2, 0.8, step=0.05),),
        max_changes=1,
    )

    assert report.chosen_id == "act"
    assert report.counterfactual_id == "escalate"
    assert report.changes[0].name == "risk"
    assert report.changes[0].new == 0.5
    assert report.distance == 0.1


def test_search_needs_two_changes() -> None:
    report = counterfactual_search(
        lambda values: "escalate" if values["risk"] + values["uncertainty"] >= 1.2 else "act",
        (
            CounterfactualVariable("risk", 0.4, 0.4, 0.7, step=0.1),
            CounterfactualVariable("uncertainty", 0.2, 0.2, 0.5, step=0.1),
        ),
        max_changes=2,
    )

    assert report.counterfactual_id == "escalate"
    assert {change.name for change in report.changes} == {"risk", "uncertainty"}
    assert report.distance == 0.6


def test_search_returns_no_counterfactual_when_none_flips() -> None:
    report = counterfactual_search(
        lambda _values: "act",
        (CounterfactualVariable("risk", 0.4, 0.2, 0.8, step=0.1),),
        max_changes=1,
    )

    assert report.counterfactual_id is None
    assert report.changes == ()
    assert report.distance == 0.0
