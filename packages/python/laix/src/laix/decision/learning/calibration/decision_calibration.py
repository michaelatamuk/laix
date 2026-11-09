"""Decision-level calibration: does a stated confidence match decision accuracy?

Prediction calibration asks whether a probability is right. Decision calibration
asks whether the *decision* was right: the verb and action that were chosen. The
report bins decisions by confidence, compares each bin with the observed share of
correct decisions, and exposes the same mapping as ``adjust``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from ...domain.decisions import Decision
from ...domain.outcomes import Outcome
from .calibration import CalibrationBin
from .decision_calibration_report import DecisionCalibrationReport
from .decision_calibration_sample import DecisionCalibrationSample


def _rate(correct: int, total: int, smoothing: float) -> float:
    return (correct + smoothing) / (total + 2.0 * smoothing) if total else 0.0


def _accuracy_by(
    items: Iterable[DecisionCalibrationSample],
    key: str,
) -> dict[str, float]:
    buckets: dict[str, list[bool]] = {}
    for item in items:
        value = getattr(item, key)
        if not value:
            continue
        buckets.setdefault(value, []).append(item.correct)
    return {
        value: round(sum(1 for flag in flags if flag) / len(flags), 6)
        for value, flags in sorted(buckets.items())
    }


def decision_calibration_report(
    samples: Iterable[DecisionCalibrationSample],
    *,
    bins: int = 10,
    policy: str = "",
    smoothing: float = 0.0,
) -> DecisionCalibrationReport:
    """Compare stated confidence with observed decision accuracy."""
    if bins < 1:
        raise ValueError("bins must be at least one")
    if smoothing < 0:
        raise ValueError("smoothing must not be negative")
    items = list(samples)
    if not items:
        return DecisionCalibrationReport(
            samples=0,
            accuracy=0.0,
            expected=0.0,
            error=0.0,
            bins=(),
            verb_accuracy={},
            action_accuracy={},
            policy=policy,
            smoothing=smoothing,
        )

    buckets: list[list[DecisionCalibrationSample]] = [[] for _ in range(bins)]
    for item in items:
        index = min(int(item.confidence * bins), bins - 1)
        buckets[index].append(item)

    rows: list[CalibrationBin] = []
    for index, bucket in enumerate(buckets):
        if not bucket:
            continue
        correct = sum(1 for item in bucket if item.correct)
        rows.append(
            CalibrationBin(
                lower=round(index / bins, 6),
                upper=round((index + 1) / bins, 6),
                predicted=round(
                    sum(item.confidence for item in bucket) / len(bucket), 6
                ),
                observed=round(_rate(correct, len(bucket), smoothing), 6),
                count=len(bucket),
            )
        )

    accuracy = sum(1 for item in items if item.correct) / len(items)
    expected = sum(item.confidence for item in items) / len(items)
    return DecisionCalibrationReport(
        samples=len(items),
        accuracy=round(accuracy, 6),
        expected=round(expected, 6),
        error=round(abs(expected - accuracy), 6),
        bins=tuple(rows),
        verb_accuracy=_accuracy_by(items, "verb"),
        action_accuracy=_accuracy_by(items, "action_id"),
        policy=policy,
        smoothing=smoothing,
    )


def decision_samples_from_outcomes(
    decisions: Iterable[Decision],
    outcomes: Iterable[Outcome],
    *,
    policies: Mapping[str, str] | None = None,
) -> tuple[DecisionCalibrationSample, ...]:
    """Turn measured outcomes into decision-level calibration samples.

    A decision counts as correct when its outcome label is ``helped``. The
    decision supplies the confidence, verb and action; the caller can map a
    decision id to a policy name.
    """
    by_id = {decision.decision_id: decision for decision in decisions}
    rows: list[DecisionCalibrationSample] = []
    for outcome in outcomes:
        decision = by_id.get(outcome.decision_id)
        if decision is None:
            continue
        rows.append(
            DecisionCalibrationSample(
                confidence=decision.confidence,
                correct=outcome.label == "helped",
                verb=decision.verb,
                action_id=decision.action_id or "",
                policy=(policies or {}).get(decision.decision_id, ""),
            )
        )
    return tuple(rows)


class CalibratedPolicy:
    """Wrap any policy and calibrate every decision it returns."""

    def __init__(
        self,
        policy: object,
        report: DecisionCalibrationReport,
        *,
        name: str | None = None,
    ) -> None:
        self.policy = policy
        self.report = report
        self.name = name or f"{getattr(policy, 'name', 'policy')}.calibrated"
        self.version = self.name

    def decide(self, request: object) -> list[Decision]:
        decisions = self.policy.decide(request)  # type: ignore[attr-defined]
        return [calibrate_decision(decision, self.report) for decision in decisions]


def calibrate_decision(
    decision: Decision,
    report: DecisionCalibrationReport,
    *,
    source: str = "decision-calibration",
) -> Decision:
    """Return a copy of ``decision`` with calibrated confidence and metadata."""
    if report.samples == 0:
        return decision
    adjusted = report.adjust(decision.confidence)
    attributes = dict(decision.attributes)
    attributes["calibration"] = {
        "before": decision.confidence,
        "after": adjusted,
        "samples": report.samples,
        "accuracy": report.accuracy,
    }
    return replace(
        decision,
        confidence=adjusted,
        calibrated=True,
        confidence_source=source,
        attributes=attributes,
    )


__all__ = [
    "CalibratedPolicy",
    "DecisionCalibrationReport",
    "DecisionCalibrationSample",
    "calibrate_decision",
    "decision_calibration_report",
    "decision_samples_from_outcomes",
]
