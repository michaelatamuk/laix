# Causal attribution

`OutcomeLedger` records whether a decision helped. `CausalLedger` estimates whether one arm caused a
better outcome. They answer different questions.

`CausalObservation` carries `decision_id`, `arm`, `outcome`, `propensity` and `context`.

`CausalEffect` carries `treatment`, `control`, `estimate`, `treated`, `control_size`, `method`,
`standard_error`, `ci_low` and `ci_high`.

| Method | Result |
|---|---|
| `add(decision_id, arm=..., outcome=..., propensity=None, context=None)` | Adds one observation. |
| `add_outcome(outcome, arm=..., signed=True)` | Maps an `Outcome`; flips the sign for `lower-better` when `signed=True`. |
| `from_outcomes(outcomes, arms, ...)` | Builds a ledger from a decision-to-arm map. |
| `effect(treatment, control)` | A `CausalEffect` for two arms. |
| `effect_by_context(treatment, control, key="stratum")` | One effect per context value; skips strata missing an arm. |

`effect` uses inverse propensity weighting when every observation carries a propensity strictly
between zero and one. Otherwise it uses the difference in means. The result includes the estimate,
the sample sizes, the method, a standard error and a 95% interval.

The propensity must be in `0..1`. A value of exactly `0` or `1` is accepted by `add`, but it cannot
be used for inverse weighting, so `effect` falls back to difference in means.

## Related

- [Outcomes](../02-domain/03-outcomes.md)
- [Calibration](01-calibration.md)
- [Causal example](../../../examples/python/core/learning/causal/causal.py)
