"""Calibration: does a stated confidence match observed accuracy?

The report is deliberately simple and auditable. It bins predictions, compares
the mean confidence in each bin with the observed success rate, and exposes the
same mapping as a calibrator so a host can adjust future confidence values.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from ...domain.outcomes import Outcome
from .calibration_bin import CalibrationBin
from .calibration_report import CalibrationReport
from .calibration_sample import CalibrationSample


def calibration_report(
    samples: Iterable[CalibrationSample],
    *,
    bins: int = 10,
    policy: str = "",
    smoothing: float = 0.0,
) -> CalibrationReport:
    """Compare stated confidence with observed accuracy.

    ``smoothing`` applies Laplace smoothing to each bin's observed rate:
    ``(correct + smoothing) / (count + 2 * smoothing)``. Zero keeps the raw
    rate; a small positive value is useful for small samples.
    """
    if bins < 1:
        raise ValueError("bins must be at least one")
    if smoothing < 0:
        raise ValueError("smoothing must not be negative")
    items = list(samples)
    if not items:
        return CalibrationReport(
            samples=0,
            accuracy=0.0,
            expected=0.0,
            error=0.0,
            bins=(),
            policy=policy,
            smoothing=smoothing,
        )

    buckets: list[list[CalibrationSample]] = [[] for _ in range(bins)]
    for item in items:
        index = min(int(item.confidence * bins), bins - 1)
        buckets[index].append(item)

    rows: list[CalibrationBin] = []
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        correct = sum(1 for item in bucket if item.correct)
        observed = (
            correct + smoothing
        ) / (len(bucket) + 2.0 * smoothing)
        rows.append(
            CalibrationBin(
                lower=round(index / bins, 6),
                upper=round((index + 1) / bins, 6),
                predicted=round(
                    sum(item.confidence for item in bucket) / len(bucket), 6
                ),
                observed=round(observed, 6),
                count=len(bucket),
            )
        )

    accuracy = sum(1 for item in items if item.correct) / len(items)
    expected = sum(item.confidence for item in items) / len(items)
    return CalibrationReport(
        samples=len(items),
        accuracy=round(accuracy, 6),
        expected=round(expected, 6),
        error=round(abs(expected - accuracy), 6),
        bins=tuple(rows),
        policy=policy,
        smoothing=smoothing,
    )


def calibration_by_policy(
    samples: Iterable[CalibrationSample],
    *,
    bins: int = 10,
    smoothing: float = 0.0,
) -> dict[str, CalibrationReport]:
    """Build one report per policy name."""
    buckets: dict[str, list[CalibrationSample]] = {}
    for item in samples:
        buckets.setdefault(item.policy, []).append(item)
    return {
        policy: calibration_report(
            items,
            bins=bins,
            policy=policy,
            smoothing=smoothing,
        )
        for policy, items in sorted(buckets.items())
    }


def samples_from_outcomes(
    outcomes: Iterable[Outcome],
    confidences: Mapping[str, float],
    *,
    policies: Mapping[str, str] | None = None,
) -> tuple[CalibrationSample, ...]:
    """Turn measured outcomes into calibration samples.

    A decision counts as correct when its outcome label is ``helped``. The
    caller supplies the confidence that was stated for each decision, and can
    optionally map a decision id to a policy name.
    """
    rows: list[CalibrationSample] = []
    for outcome in outcomes:
        confidence = confidences.get(outcome.decision_id)
        if confidence is None:
            continue
        rows.append(
            CalibrationSample(
                confidence=confidence,
                correct=outcome.label == "helped",
                policy=(policies or {}).get(outcome.decision_id, ""),
            )
        )
    return tuple(rows)


__all__ = [
    "CalibrationBin",
    "CalibrationReport",
    "CalibrationSample",
    "calibration_by_policy",
    "calibration_report",
    "samples_from_outcomes",
]
