# CABB: commitment-attention branch and bound

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

## Related

- [Sequence overview](README.md)
- [Rollout](02-rollout.md)
- [Replan](03-replan.md)
