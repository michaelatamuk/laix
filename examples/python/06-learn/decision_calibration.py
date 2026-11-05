"""Calibrate the decision, not just the confidence."""

from __future__ import annotations

from laix import (
    Decision,
    DecisionCalibrationSample,
    calibrate_decision,
    decision_calibration_report,
)

samples = [
    DecisionCalibrationSample(confidence=0.9, correct=index < 5)
    for index in range(10)
]
report = decision_calibration_report(samples)
decision = Decision(
    verb="act",
    confidence=0.9,
    reason_code="expected_utility",
    rationale="the valve is the best option",
    decision_id="d1",
    action_id="valve",
)
calibrated = calibrate_decision(decision, report)

print(decision.confidence, calibrated.confidence, calibrated.confidence_source)
