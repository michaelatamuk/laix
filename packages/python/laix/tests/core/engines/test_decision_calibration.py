"""Decision-level calibration: the decision, not just the probability."""

from __future__ import annotations

import pytest

from laix import (
    CalibratedPolicy,
    Decision,
    DecisionCalibrationReport,
    DecisionCalibrationSample,
    DecisionRequest,
    Outcome,
    calibrate_decision,
    decision_calibration_report,
    decision_samples_from_outcomes,
)


def test_report_bins_decisions_and_adjusts_confidence() -> None:
    samples = [
        *[DecisionCalibrationSample(0.9, True, verb="act", action_id="send") for _ in range(8)],
        *[DecisionCalibrationSample(0.9, False, verb="act", action_id="send") for _ in range(2)],
        *[DecisionCalibrationSample(0.2, True, verb="wait") for _ in range(2)],
        *[DecisionCalibrationSample(0.2, False, verb="wait") for _ in range(8)],
    ]
    report = decision_calibration_report(samples)

    assert report.samples == 20
    assert report.accuracy == 0.5
    assert report.expected == 0.55
    assert report.error == 0.05
    assert report.adjust(0.9) == 0.8
    assert report.adjust(0.2) == 0.2
    assert report.verb_accuracy["act"] == 0.8
    assert report.action_accuracy["send"] == 0.8


def test_report_round_trips_through_a_dict() -> None:
    report = decision_calibration_report(
        [DecisionCalibrationSample(0.9, index < 5) for index in range(10)]
    )
    restored = DecisionCalibrationReport.from_dict(report.to_dict())

    assert restored.samples == report.samples
    assert restored.accuracy == report.accuracy
    assert restored.adjust(0.9) == report.adjust(0.9)


def test_empty_report_is_neutral() -> None:
    report = decision_calibration_report([])

    assert report.samples == 0
    assert report.bins == ()
    assert report.adjust(0.7) == 0.7
    assert report.to_dict()["verb_accuracy"] == {}


def test_calibrate_decision_preserves_the_decision() -> None:
    report = decision_calibration_report(
        [DecisionCalibrationSample(0.9, index < 5) for index in range(10)]
    )
    decision = Decision(
        verb="act",
        confidence=0.9,
        reason_code="expected_utility",
        rationale="the valve is the best option",
        decision_id="d1",
        action_id="valve",
    )

    calibrated = calibrate_decision(decision, report)

    assert calibrated.confidence == 0.5
    assert calibrated.calibrated is True
    assert calibrated.confidence_source == "decision-calibration"
    assert calibrated.verb == "act"
    assert calibrated.action_id == "valve"
    assert calibrated.attributes["calibration"]["before"] == 0.9
    assert calibrated.attributes["calibration"]["after"] == 0.5


def test_calibrated_policy_wraps_any_policy() -> None:
    class FakePolicy:
        name = "fake"

        def decide(self, request: object) -> list[Decision]:
            return [
                Decision(
                    verb="act",
                    confidence=0.9,
                    reason_code="fake",
                    rationale="a fake decision",
                    decision_id="d1",
                )
            ]

    report = decision_calibration_report(
        [DecisionCalibrationSample(0.9, index < 5) for index in range(10)]
    )
    policy = CalibratedPolicy(FakePolicy(), report)
    decisions = policy.decide(
        DecisionRequest(subject="a", at="2026-11-01T10:00:00+00:00")
    )

    assert policy.name == "fake.calibrated"
    assert decisions[0].confidence == 0.5
    assert decisions[0].calibrated is True


def test_samples_from_outcomes_use_the_decision_shape() -> None:
    decision = Decision(
        verb="act",
        confidence=0.8,
        reason_code="r",
        rationale="why",
        decision_id="d1",
        action_id="a1",
    )
    outcome = Outcome(
        id="o1",
        decision_id="d1",
        metric="saved",
        before=0.0,
        after=1.0,
        delta=1.0,
        label="helped",
    )

    samples = decision_samples_from_outcomes([decision], [outcome])

    assert len(samples) == 1
    assert samples[0].correct is True
    assert samples[0].verb == "act"
    assert samples[0].action_id == "a1"


def test_invalid_arguments_are_rejected() -> None:
    with pytest.raises(ValueError):
        decision_calibration_report([], bins=0)
    with pytest.raises(ValueError):
        decision_calibration_report([], smoothing=-1.0)
