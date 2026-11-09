# Calibration

Calibration checks whether confidence matches observed accuracy, and whether a decision policy becomes
better when its confidence is adjusted.

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

## Decision calibration

`DecisionCalibrationReport` applies the same idea to decisions. `calibrate_decision` changes the
confidence on a `Decision` without changing its verb, action or trace. `CalibratedPolicy` wraps any
policy and calibrates its output.

```python
from laix import CalibratedPolicy, calibrate_decision

adjusted = calibrate_decision(decision)
policy = CalibratedPolicy(inner_policy)
```

## Where it fits

Calibration is a learner, not a planner. It does not choose options; it changes how much the next
consumer should trust the confidence.

## Related

- [Outcomes](../02-domain/03-outcomes.md)
- [Model learning](02-model.md)
- [Decision calibration example](../../../examples/python/decision/learning/calibration/calibration.py)
- [Calibration report API](../../05-project/01-repository/02-api-map.md)
