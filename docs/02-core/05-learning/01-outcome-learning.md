# Outcome learning

Outcome learning turns a measured result into a reward, updates a choice and improves the next
decision.

```text
decision → outcome → reward → learner → next decision
```

The app measures the outcome. LAIX owns the reward contract, the learner and the policy shape.

## Outcome

`Outcome` is the measured result of one decision:

| Field | Meaning |
|---|---|
| `id` | Outcome id. |
| `decision_id` | The decision that produced it. |
| `metric` | The measured quantity. |
| `before`, `after` | The values before and after the decision. |
| `delta` | `after - before`. |
| `label` | `helped`, `neutral`, `hurt` or `unknown`. |
| `direction` | `higher-better` or `lower-better`. |
| `attributed` | Whether the outcome is attributed to the decision. |
| `evidence` | Host-owned detail. |
| `measured_at` | When the outcome was measured. |
| `note` | Host note. |
| `schema_version` | The record version. |

`Outcome.__post_init__` rejects an unknown label or direction. `to_dict()` serialises it.

## Outcome ledger

`OutcomeLedger` is the in-memory store. Its main method records a measurement and derives the label:

```python
from laix import OutcomeLedger

ledger = OutcomeLedger()
outcome = ledger.record(
    "DEC-1",
    metric="resolution_time",
    before=120.0,
    after=90.0,
    direction="lower-better",
    attributed=True,
)
print(outcome.label)  # helped
```

The label rule:

```text
gain = delta        if direction == "higher-better"
       -delta       if direction == "lower-better"

gain > tolerance      -> helped
gain < -tolerance     -> hurt
otherwise             -> neutral
```

`tolerance` defaults to `1e-9`. An explicit `label` overrides the derived value.

| Method | Result |
|---|---|
| `record(decision_id, ...)` | Builds, stores and returns one `Outcome`. |
| `add(outcome)` | Stores an existing outcome. |
| `for_decision(decision_id)` | The outcomes for one decision. |
| `all()` | Every outcome. |
| `extend(outcomes)` | Adds several outcomes. |
| `summary()` | `measured`, `attributed`, `attributionCoverage`, `helped`, `neutral`, `hurt`, `meanGain`, `precision`. |
| `by_metric()` | Per metric: `measured`, `attributed`, `helped`, `hurt`, `gain`. |
| `to_dict()` | `tolerance`, `records`, `summary`. |

`OutcomeStore` is the persistence port: `add`, `for_decision`, `all`, `summary`. The host implements
it with its own database.

## Rewards

`reward_for_label` maps a label to a reward:

| Label | Reward |
|---|---:|
| `helped` | 1.0 |
| `neutral` | 0.5 |
| `hurt` | 0.0 |
| `unknown` | `None` (skip) |

## Arm and UCB learner

`Arm` is one choice:

| Field | Default | Meaning |
|---|---:|---|
| `id` | required | Arm id. |
| `prior_mean` | 0.5 | Starting reward estimate. |
| `prior_weight` | 1.0 | How strongly the prior counts. |
| `cost` | 0.0 | Cost of choosing the arm. |
| `risk` | 0.0 | Risk of choosing the arm. |

`UCBBandit` uses an **upper confidence bound**: it picks the arm with the best reward plus a bonus
for arms tried less, so an untried arm gets a chance.

```python
from laix import Arm, UCBBandit

bandit = UCBBandit([Arm("manual"), Arm("automatic")])
bandit.choose()          # tries an untried arm first
bandit.update("manual", 0.0)
bandit.update("automatic", 1.0)
bandit.choose()          # now picks automatic
```

The learned mean is:

```text
mean = (prior_mean × prior_weight + total_reward) / max(prior_weight + pulls, 1e-9)
```

The choice score is:

```text
∞                                      if pulls == 0
mean + exploration × sqrt(log(total_pulls + 1) / pulls)   otherwise
```

`exploration` defaults to `1.4`.

| Method | Meaning |
|---|---|
| `add(arm)` | Adds or replaces an arm definition; existing pulls and rewards stay. |
| `update(arm_id, reward)` | Records one reward in `0..1`. |
| `learn(outcomes, arm_of)` | Learns from labelled outcomes; skips `unknown`; returns the used count. |
| `mean(arm_id)` | The learned reward. |
| `score(arm_id)` | Reward plus exploration. |
| `choose(max_risk, budget, exclude)` | The best arm inside the limits, or `None`. |
| `pulls(arm_id)` | The number of updates. |
| `to_dict()` | Exploration and per-arm state. |

`BanditPolicy` puts the learner behind the policy interface. It reads arms from
`DecisionRequest.attributes["arms"]` or from the bandit, respects `max_risk`, `budget` and
`exclude`, and returns `act` with `bandit_choice`, or `wait` with `no_arms` or
`no_arm_within_limits`. See [Policies](../02-decide/03-policies.md#learned-policy).

## Causal attribution

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

## Attention outcomes

Signal attention has its own outcome shapes:

- `AttentionOutcome` carries `signal_id`, `kind`, `verb`, `result`, `reason_code`, `score` and `at`.
- `OutcomeLog` keeps the latest `limit` records (default 500) and reports `total`, `precision`,
  `hazard_rate`, `adjustment`, `calibration` and `by_kind`.
- `labels.py` maps a feedback state and reason to a result: `accepted`/`confirmed`/`signed` →
  `helped`; `wrong`/`false_alarm` → `hurt`; `dismissed`/`snoozed`/`assigned` → a reason-based
  neutral or hurt; otherwise `unknown`.

`OutcomeLog.adjustment(kind, weight=12.0)` returns a per-kind point adjustment. A host can place it
in `Context.learned` so the next signal decision uses it.

## What the app owns

The app owns the metric, the measurement, the decision-to-arm map and the feedback state. LAIX owns
the reward contract, the ledger, the learner and the policy shape.

## Example

`examples/python/02-policies/bandit.py`:

```text
manual automatic 0.75
```

## Related

- [Policies](../02-decide/03-policies.md#learned-policy) — `BanditPolicy`
- [Calibration and model learning](02-calibration-and-model-learning.md)
- [Evaluation](../06-reference/01-evaluation.md)
- [Stores](../../03-appkit/04-connect/01-stores.md) — `OutcomeStore`
