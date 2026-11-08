# Decision value (CA-VOD)

`CAVODPlanner` is a single-decision planner. It starts from the same four live terms as
`LiveCompositePlanner` and adds:

- `information` for `ask`, `verify` and `observe`;
- `option` for `wait`.

The information value is `information_weight * uncertainty * information_gain`. The option value is
`waiting_weight * uncertainty`. The host can override either value in the option's `params`:

```python
from laix import ActionOption, CAVODPlanner, PlannerInput

plan = CAVODPlanner().solve(
    PlannerInput(
        subject="invoice 4832",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.6),
            ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
        ),
        attributes={"uncertainty": 0.8},
    )
)
print(plan.action_id, plan.attributes["information_value"])
```

`CAVODPlanner` implements the `Planner` protocol, so it works behind `PlannerPolicy`:

```python
from laix import CAVODPlanner, PlannerPolicy, decide

# request is the DecisionRequest built in the one-decision example.
decision = decide(request, policy=PlannerPolicy(CAVODPlanner(), name="ca_vod.v1"))[0]
```

The default path is one-step. Pass a `PomdpModel` and a belief to add a finite-horizon
belief-state future value without double-counting the immediate reward:

```python
from laix import CAVODPlanner, PomdpModel

planner = CAVODPlanner(
    pomdp_model=model,
    belief={"safe": 0.5, "risky": 0.5},
)
```

The future-value path uses the `action_future_value` helper from the POMDP planner. The full
constrained POMDP with hard commitment and attention constraints in the transition model remains
research work.

## Limits

CA-VOD is a one-step value of decision with an optional finite-horizon belief lookahead. It is not a
constrained POMDP solver and it does not prove that information or waiting is always worth more.

## Examples

- Python: `examples/python/core/decision/single/planners/ca_vod_planner.py`
- Python: `examples/python/core/decision/single/planners/ca_vod_belief.py`
- TypeScript: `examples/typescript/core/decision/single/planners/ca_vod_planner.mts`
- TypeScript: `examples/typescript/core/decision/single/planners/ca_vod_belief.mts`

## Related

- [Composite planner](02-composite.md)
- [Model-based planners](03-model-based.md)
- [Algorithm directions](../../../06-research/01-positioning/04-algorithm-directions.md)
- [Algorithm prototype results](../../../06-research/02-evaluation/algorithm-prototypes.md)
