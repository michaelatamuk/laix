# Bandit and rewards

A bandit turns labelled outcomes into a better next choice. The outcome record is in
[Domain / outcomes](../02-domain/03-outcomes.md); this page covers the reward mapping and the learner.

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
`no_arm_within_limits`. See [Policies](../03-decision-shapes/06-policies/02-packaged-policies.md#learned-policy).

## Related

- [Outcomes](../02-domain/03-outcomes.md)
- [Policies](../03-decision-shapes/06-policies/README.md)
- [Bandit example](../../../examples/python/decision/decision/single/policies/bandit.py)
