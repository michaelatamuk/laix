# Sequence planning

A `Planner` answers one live decision. A `SequencePlanner` answers a chain: one option at each step of
a known horizon, under open commitments and a shared human-attention budget.

| Class | Use |
|---|---|
| `CABBPlanner` | exact best chain for a small deterministic scenario |
| `RolloutPlanner` | good-enough chain for a larger horizon; greedy completion of each first option |
| `ReplanPlanner` | rebuild the remaining chain after an executed prefix |

## CABB: commitment-attention branch and bound

`CABBPlanner` searches the whole chain and returns the exact best chain for the supplied finite
deterministic scenario.

```python
from laix import (
    ActionOption,
    CABBPlanner,
    Commitment,
    DecisionScenario,
    DecisionStep,
    HumanAttentionBudget,
)

scenario = DecisionScenario(
    steps=(
        DecisionStep(
            at="2026-11-01T10:00:00+00:00",
            options=(
                ActionOption(
                    id="pay",
                    verb="act",
                    name="pay",
                    expected_benefit=0.95,
                    requires_approval=True,
                    reversible=False,
                    params={"commitments": {"violates": ["c1"]}},
                ),
                ActionOption(
                    id="ask",
                    verb="ask",
                    name="ask",
                    expected_benefit=0.6,
                    params={"commitments": {"fulfills": ["c1"]}},
                ),
            ),
        ),
        DecisionStep(
            at="2026-11-01T11:00:00+00:00",
            options=(
                ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
                ActionOption(id="verify", verb="verify", name="verify", expected_benefit=0.4),
            ),
        ),
    ),
    commitments=(
        Commitment(
            id="c1",
            subject="ask before paying",
            due="2026-11-01T09:00:00+00:00",
        ),
    ),
    human_attention_budget=HumanAttentionBudget(total=2.0, spent=0.5),
)

plan = CABBPlanner().plan(scenario)
print(plan.actions, plan.score, plan.optimal)
```

`CABBPlanner` also exposes `evaluate` for a fixed chain and `advance` for a state update after a
prefix. The exact guarantee applies only to the finite deterministic scenario.

## Rollout and replan

`RolloutPlanner` uses CABB's evaluator for each option at the current step and completes the rest
greedily. It is bounded by the horizon and is not exact.

`ReplanPlanner` replays an executed prefix, then calls CABB on the remaining steps. It is the recovery
layer after a failure or refusal.

```python
from laix import ReplanPlanner, RolloutPlanner

approximate = RolloutPlanner().plan(scenario)
recovery = ReplanPlanner().replan(scenario, ("ask",))
print(approximate.actions, recovery.actions)
```

## Limits

CABB is exact only for a finite deterministic scenario. Rollout is approximate. Replan is a recovery
layer, not a new guarantee. An uncertain or infinite-horizon version remains research work.

## Related

- [Single decision](01-single/README.md)
- [Fleet](03-fleet.md)
- [History](04-history.md)
- [Algorithm directions](../../06-research/01-positioning/04-algorithm-directions.md)
- [Algorithm prototype results](../../06-research/02-evaluation/algorithm-prototypes.md)
