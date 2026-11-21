# Calibration

Calibration checks whether confidence matches observed accuracy, and whether a decision policy becomes
better when its confidence is adjusted. It is optional: LAIX runs without it, and the default
training-free path does not calibrate anything.

## Prediction calibration

`CalibrationReport` groups samples into reliability bins. A bin compares the mean confidence with the
observed success rate, so a policy that says “0.9” and is right 60% of the time is visible.

```python
from laix import CalibrationSample, calibration_report

report = calibration_report(
    (
        CalibrationSample(confidence=0.9, correct=True),
        CalibrationSample(confidence=0.8, correct=False),
        CalibrationSample(confidence=0.6, correct=True),
    )
)
print(report.bins)
```

`error` is the global gap between expected confidence and observed accuracy. Read the bins to see
where the gap comes from; an empty bin carries no evidence.

## Decision calibration

`DecisionCalibrationReport` applies the same idea to decisions. `calibrate_decision` changes the
confidence on a `Decision` without changing its verb, action or trace. `CalibratedPolicy` wraps any
policy and calibrates its output.

```python
from laix import (
    CalibratedPolicy,
    calibrate_decision,
    decision_calibration_report,
    decision_samples_from_outcomes,
)

samples = decision_samples_from_outcomes(decisions, outcomes)
report = decision_calibration_report(samples, bins=10, smoothing=0.5)

adjusted = calibrate_decision(decision, report)
policy = CalibratedPolicy(inner_policy, report)
```

Both calls require the report. When `report.samples == 0`, `calibrate_decision` returns the decision
unchanged, so calibration is a no-op until there is data.

## When to calibrate

Calibrate when confidence is consumed as a probability or a comparison:

- a confidence floor gates attention, escalation, approval or delivery;
- confidence arbitrates between policies or planners;
- a person reads confidence as a probability;
- you have measured outcomes with a defensible “correct” label.

Skip it when:

- a rule with a fixed reason code makes the decision and confidence is decorative;
- there are no labelled outcomes, or attribution is weak;
- samples are tiny or sparse per action;
- the policy itself is wrong. Calibration remaps confidence; it does not fix the utility model,
  constraints or the options the host offered.

## Fit it from outcomes

1. Record outcomes with `DecisionClient.measure` or the outcome ledger.
2. Use **attributed** outcomes only. Decision calibration counts a decision as correct when the
   outcome label is `helped`; an unattributed label is not evidence that the decision caused it.
3. Build a report **per policy**. Do not pool policies with different behaviour. Inspect
   `verb_accuracy` and `action_accuracy` before trusting a small per-action slice.
4. Require a minimum sample size. There is no built-in threshold beyond the `samples == 0` no-op:
   set one in the host, require populated bins, and use `smoothing` for small bins.
5. Apply with `CalibratedPolicy` or `calibrate_decision`. The decision keeps its verb, action and
   trace; it gains `calibrated = true`, a `confidence_source`, and the before/after/samples/accuracy
   in its attributes.
6. Re-fit on a schedule, watch the bins for drift, and keep the uncalibrated policy for rollback.

The Kotlin package exposes the same names in camelCase: `decisionSamplesFromOutcomes`,
`decisionCalibrationReport`, `calibrateDecision` and `CalibratedPolicy`.

## Where it fits

Calibration is a learner, not a planner. It does not choose options; it changes how much the next
consumer should trust the confidence. The adjustment is a binned reliability map with a global-shift
fallback — simple and auditable, not a replacement for a proper probability model.

## Related

- [Outcomes](../02-domain/03-outcomes.md)
- [Model learning](02-model.md)
- [Decision calibration example](../../../examples/python/decision/learning/calibration/calibration.py)
- [Calibration report API](../../06-project/01-repository/02-api-map.md)
