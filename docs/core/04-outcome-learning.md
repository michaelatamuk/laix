# Outcome learning

LAIX learns from measured outcomes, turns the result into a reward, and improves the next choice.

| Word | Meaning |
|---|---|
| **Outcome** | A measured result of a decision. |
| **Reward** | A number from `0` to `1` that says how good the outcome was. |
| **Arm** | One choice the learner can pick. |
| **Learner** | Code that updates its choice from rewards. |
| **Ledger** | A store of measured outcomes. |

```text
decision -> outcome -> reward -> learner -> next decision
```

## Rewards

```python
from laix import reward_for_label

reward_for_label("helped")   # 1.0
reward_for_label("neutral")  # 0.5
reward_for_label("hurt")     # 0.0
reward_for_label("unknown")  # None: skip
```

An `Outcome` stores the decision id, metric, before/after, label, attribution and evidence. The app
measures it. LAIX learns from the label.

## Learner

```python
from laix import Arm, OutcomeLedger, UCBBandit

ledger = OutcomeLedger()
bandit = UCBBandit([Arm("manual"), Arm("automatic")])
bandit.choose()          # tries an untried arm first
bandit.update("manual", 0.0)
bandit.update("automatic", 1.0)
bandit.choose()          # now picks automatic
```

| Method | Meaning |
|---|---|
| `add(arm)` | add an arm |
| `update(arm_id, reward)` | record a reward in `0..1` |
| `choose(max_risk, budget)` | pick the best arm inside the limits |
| `learn(outcomes, arm_of)` | learn from labelled outcomes |
| `mean(arm_id)` | learned reward |
| `score(arm_id)` | reward plus exploration |

An arm has `id`, `prior_mean`, `prior_weight`, `cost` and `risk`.

Learn from a ledger:

```python
used = bandit.learn(
    ledger.all(),
    lambda decision_id: arm_by_decision[decision_id],
)
```

## Policy

```python
from laix import BanditPolicy, decide

policy = BanditPolicy(bandit)
decision = decide(request, policy=policy)[0]

policy.record("automatic", 1.0)
policy.learn(ledger.all(), lambda decision_id: arm_by_decision[decision_id])
```

The policy reads arms from `DecisionRequest.attributes["arms"]` or from the bandit. It respects
`max_risk`, `budget` and `exclude`.

No arms returns `wait` with `no_arms`. All arms outside the limits returns `wait` with
`no_arm_within_limits`.

## Causal attribution

`CausalLedger` compares a treatment arm with a control arm. It uses difference in means, or inverse
propensity weighting when every observation carries a propensity strictly between zero and one. It
returns a `CausalEffect` with the estimate, the sample sizes and the method.

`OutcomeLedger` records whether a decision helped; `CausalLedger` estimates whether one arm caused a
better outcome. They answer different questions.

## App and LAIX

The app owns the metric, the measurement and the decision-to-arm map. LAIX owns the reward contract,
the learner and the policy shape.

TypeScript exports `UCBBandit`, `BanditPolicy`, `Arm` and `rewardForLabel`.

## Example

`examples/policies/bandit.py`:

```text
manual automatic 0.75
```
