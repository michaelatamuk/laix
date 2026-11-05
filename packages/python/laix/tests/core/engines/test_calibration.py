"""Confidence calibration."""

from __future__ import annotations

from laix import (
    CalibrationSample,
    calibration_by_policy,
    calibration_report,
    samples_from_outcomes,
)
from laix import Outcome


def _samples(policy: str = "") -> list[CalibrationSample]:
    return [
        CalibrationSample(confidence=0.9, correct=index < 5, policy=policy)
        for index in range(10)
    ]


def test_report_compares_expected_and_observed() -> None:
    report = calibration_report(_samples())

    assert report.samples == 10
    assert report.expected == 0.9
    assert report.accuracy == 0.5
    assert report.error == 0.4
    assert report.bins[0].count == 10
    assert report.bins[0].observed == 0.5


def test_adjust_uses_the_observed_rate() -> None:
    report = calibration_report(_samples())

    assert report.adjust(0.9) == 0.5


def test_reports_are_grouped_by_policy() -> None:
    reports = calibration_by_policy(_samples("rules") + _samples("bandit"))

    assert sorted(reports) == ["bandit", "rules"]
    assert reports["rules"].samples == 10


def test_outcomes_become_samples() -> None:
    outcomes = [
        Outcome(
            id="o1",
            decision_id="d1",
            metric="precision",
            before=0.5,
            after=0.8,
            delta=0.3,
            label="helped",
        ),
        Outcome(
            id="o2",
            decision_id="d2",
            metric="precision",
            before=0.5,
            after=0.4,
            delta=-0.1,
            label="hurt",
        ),
    ]
    samples = samples_from_outcomes(
        outcomes,
        {"d1": 0.8, "d2": 0.7},
        policies={"d1": "rules", "d2": "rules"},
    )

    assert [item.correct for item in samples] == [True, False]
    assert {item.policy for item in samples} == {"rules"}
