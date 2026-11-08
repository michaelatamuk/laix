# Simulation

`Simulator` runs a planner through a deterministic step function. It is the way to compare planners
on the same trace.

| Type | Fields or methods |
|---|---|
| `Simulator` | `step`, `actions`, `start`, `horizon`, `name`, `random_step`, `seed`; `run(planner)`, `from_mdp(model, start=None, seed=None)` |
| `Scenario` | `name`, `simulator`, `optimum`; `run(planner)` |
| `SimulationStep` | `step`, `state`, `action`, `reward`, `next_state` |
| `SimulationResult` | `scenario`, `steps`, `total_reward`, `final_state`; `summary()` |
| `PlannerBenchmarkRow` | `planner`, `scenario`, `total_reward`, `steps`, `optimality_gap` |
| `SimulationReport` | `rows`; `summary()`, `best()`, `to_dict()` |

`SimulationReport.summary()` groups by planner and returns `runs`, `mean_reward` and `mean_gap`.
`best()` returns the planner with the highest mean reward. `SimulationResult.summary()` returns the
scenario, the step count, the total reward and the final state.

`compare_planners(planners, scenarios)` runs every planner on every scenario.
`seeded_scenarios(seed, *, count=3, horizon=8, actions=("a", "b"))` builds repeatable chains with a
known optimum. `Simulator.from_mdp(model, seed=...)` builds a deterministic or seeded stochastic rollout
from an `MdpModel`.

```python
from laix import MDPPlanner, Scenario, Simulator, UtilityPlanner, compare_planners

scenario = Scenario(
    name="forward-chain",
    simulator=Simulator.from_mdp(model),  # model: MdpModel
    optimum=4.0,
)

report = compare_planners(
    {"mdp": MDPPlanner(model), "utility": UtilityPlanner()},
    [scenario],
)
print(report.summary())
print(report.best())
```

The optimality gap is:

```text
gap = max(0, (optimum - total_reward) / max(|optimum|, 1e-9))
```

It is reported only when the scenario declares an optimum. Without an optimum, `optimality_gap` is
`None` and the summary treats it as `0.0`.

## Related

- [Cases and parity](01-cases.md)
- [Benchmarks](02-bench.md)
- [Planner contract](../01-contract/02-planner-contract.md)
- [Simulator example](../../../examples/python/core/evaluation/simulation/simulator.py)
