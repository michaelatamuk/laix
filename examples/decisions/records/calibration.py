"""Compare stated confidence with observed accuracy."""

from __future__ import annotations

from laix import CalibrationSample, calibration_report

report = calibration_report(
    [CalibrationSample(confidence=0.9, correct=index < 5) for index in range(10)]
)
print(report.expected, report.accuracy, report.error, report.adjust(0.9))
