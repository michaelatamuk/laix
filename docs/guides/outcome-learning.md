# Outcome learning

Outcome learning closes the loop:

```text
decision -> measured outcome -> reward -> learner -> next decision
```

Recording measures what happened. Learning uses those measurements to change the next choice.

## Labels and rewards

```python
from laix import reward_for_label

reward_for_label("helped")   # 1.0
reward_for_label("neutral")  # 0.5
reward_for_label("hurt")     # 0.0
reward_for_label("unknown")  # None: skip it
```

An `Outcome` carries the decision id, metric, before/after values, label, attribution and evidence.
The app measures the outcome; LAIX learns from the label.

## The learner

`UCBBandit` is a deterministic upper-confidence-bound learner over named arms. Determinism keeps
replay and tests stable.

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

## Learning from a ledger

`learn` needs the arm that produced each decision:

```python
used = bandit.learn(
    ledger.all(),
    lambda decision_id: arm_by_decision[decision_id],
)
```

Outcomes labelled `unknown` are skipped.

## The policy

`BanditPolicy` puts the learner behind the policy interface:

```python
from laix import BanditPolicy, Layer

policy = BanditPolicy(bandit)
decision = Layer(policy=policy).decide(request)[0]

policy.record("automatic", 1.0)
policy.learn(ledger.all(), lambda decision_id: arm_by_decision[decision_id])
```

- It reads arms from `DecisionRequest.attributes["arms"]` or from the bandit itself.
- It respects `max_risk`, `budget` and `exclude`.
- It returns `act` with an `act` intent naming the chosen arm.
- `record(arm_id, reward)` records one reward.
- `learn(outcomes, arm_of)` learns from a ledger.

No arms returns `wait` with `no_arms`. Every arm outside the limits returns `wait` with
`no_arm_within_limits`.

## TypeScript

The TypeScript package exports `UCBBandit`, `BanditPolicy`, `Arm` and `rewardForLabel` with the same
behaviour.

## App and layer

The app owns the metric, the measurement and the mapping from decisions to arms. LAIX owns the reward
contract, the learner and the policy shape. A different learner can replace UCB while the outcome
record and policy interface stay the same.

## Example

`examples/python/policies/bandit.py`:

```text
manual automatic 0.75
```
