# Outcome learning

Outcome learning closes the loop:

```text
decision -> measured outcome -> reward -> learner -> next decision
```

Recording an outcome is not learning. The learner turns labels into rewards and changes what the
policy chooses next.

## Contract

```python
from laix import Outcome, reward_for_label

reward_for_label("helped")   # 1.0
reward_for_label("neutral")  # 0.5
reward_for_label("hurt")     # 0.0
reward_for_label("unknown")  # None: skip it
```

`Outcome` stays the canonical record: decision id, metric, before/after, label, attribution and
evidence. The app measures the outcome; LAIX learns from the label.

## The learner

`UCBBandit` is a deterministic upper-confidence-bound learner over named arms. UCB is used instead
of Thompson sampling so replay and tests are stable.

```python
from laix import Arm, UCBBandit

bandit = UCBBandit([Arm("manual"), Arm("automatic")])
bandit.choose()          # explores an untried arm first
bandit.update("manual", 0.0)
bandit.update("automatic", 1.0)
bandit.choose()          # now prefers automatic
```

| Method | Meaning |
|---|---|
| `add(arm)` | register an arm |
| `update(arm_id, reward)` | record one reward in `0..1` |
| `choose(max_risk, budget, exclude)` | pick the best arm inside the limits |
| `learn(outcomes, arm_of)` | update from labelled outcomes |
| `mean(arm_id)` | learned reward, including the prior |
| `score(arm_id)` | mean plus the exploration bonus |
| `to_dict()` | serialisable snapshot |

An arm carries `id`, `prior_mean`, `prior_weight`, `cost` and `risk`.

## The policy

`BanditPolicy` puts the learner behind the policy interface:

```python
from laix import BanditPolicy, Layer

layer = Layer(policy=BanditPolicy(bandit))
decision = layer.decide(request)[0]
```

- It reads arms from `DecisionRequest.attributes["arms"]` or from the bandit itself.
- It respects `max_risk`, `budget` and `exclude`.
- It returns `act` with an `act` intent naming the chosen arm.
- `policy.record(arm_id, reward)` records one reward.
- `policy.learn(outcomes, arm_of)` learns from a ledger.

No arms returns `wait` with `no_arms`. Every arm outside the limits returns `wait` with
`no_arm_within_limits`.

## Boundary

The app owns the metric, the measurement and the mapping from a decision to an arm. LAIX owns the
reward contract, the learner and the policy shape. Swap UCB for another learner without changing the
outcome record or the policy interface.

## Example

`examples/python/policies/bandit.py`:

```text
manual automatic 0.75
```
