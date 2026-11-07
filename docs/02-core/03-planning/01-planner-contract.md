# The planner contract

Planners are optional. A host can use signal attention and the packaged policies without a planner.
A planner adds a formal choice over the options the host already supplied.

The contract has three pieces:

- `PlannerInput` goes in;
- `PlannerResult` comes out;
- `Planner` is the `solve` interface.

`PlannerPolicy` adapts a planner or composite planner to the policy interface.

## `PlannerInput`

`PlannerInput` is the planner input. `to_planner_input` projects a `DecisionRequest` onto it.

| Field | Type | Meaning |
|---|---|---|
| `subject` | `str` | What the problem is about. |
| `at` | ISO-8601 `str` | The decision moment. |
| `situation` | `Situation \| None` | Observations, beliefs, goals and constraints. |
| `options` | `tuple[ActionOption, ...]` | Actions the planner may choose. |
| `signals` | `tuple` | Signals, when the planner needs them. |
| `context` | `SignalContext \| None` | Signal context, when the planner needs it. |
| `attributes` | `dict` | Planner-specific state and inputs. |

The projection carries `subject`, `at`, `situation`, `options`, `signals`, `context` and
`attributes` from the request. Target, recipients, deadline and confidence belong to the delivery
envelope; the planner works on the problem.

## `PlannerResult`

`PlannerResult` is the planner answer, before it becomes a `Decision`.

| Field | Type | Meaning |
|---|---|---|
| `verb` | `str` | The chosen verb. |
| `confidence` | `float` | The planner confidence, `0..1`. |
| `reason_code` | `str` | The planner reason. |
| `rationale` | `str` | Human-readable explanation. |
| `action_id` | `str \| None` | The chosen option. |
| `intent` | `Intent \| None` | The action the host can execute. |
| `requires_approval` | `bool` | A person must approve. |
| `reversible` | `bool` | The chosen option can be undone. |
| `undo_hint` | `str \| None` | How to undo it. |
| `score` | `float \| None` | The planner ranking value. |
| `alternatives` | `tuple[dict, ...]` | Options that lost and why. |
| `attributes` | `dict` | Planner-specific breakdown. |

A planner returns one `PlannerResult`. `PlannerPolicy` converts it into one `Decision`.

## `Planner`

```python
class Planner(Protocol):
    def solve(self, problem: PlannerInput) -> PlannerResult: ...
```

Every built-in planner and `LiveCompositePlanner` implements this method. An external planner can
implement it too.

## `PlannerPolicy`

`PlannerPolicy` is the bridge between the two shapes:

```python
from laix import PlannerInput, PlannerPolicy, PlannerResult

policy = PlannerPolicy(planner)
decision = policy.decide(request)[0]
```

| Member | Meaning |
|---|---|
| `planner` | The `Planner` instance. |
| `name` | The policy name; `"planner.v1"` by default. |
| `version` | Same as `name`. |
| `decide(request, *, decision_id="", trace_id="")` | Projects, solves and converts. |

The conversion is `to_decision(planner_result, request, ...)`:

- copies the planner result fields onto `Decision`;
- sets `policy_version` to the `PlannerPolicy` name;
- merges `request.attributes` and `planner_result.attributes`, with the planner result winning on a key collision.

`to_planner_input` and `to_decision` are public. An adapter that calls a composite planner directly can use them, so
every planner path returns the same `Decision`.

## Sequence

```mermaid
sequenceDiagram
    participant Host
    participant DecisionPolicy as PlannerPolicy
    participant CompositePlanner as Planner
    participant Convert as to_decision
    Host->>DecisionPolicy: decide(DecisionRequest)
    DecisionPolicy->>DecisionPolicy: to_planner_input(request)
    DecisionPolicy->>CompositePlanner: solve(PlannerInput)
    CompositePlanner-->>DecisionPolicy: PlannerResult
    DecisionPolicy->>Convert: to_decision(planner_result, request)
    Convert-->>DecisionPolicy: Decision
    DecisionPolicy-->>Host: [Decision]
```

## External planners

An external planner can be a classifier, an optimizer or a model service. Wrap it in a thin adapter
that returns a `PlannerResult`:

```python
from laix import PlannerInput, PlannerPolicy, PlannerResult

class MyPlanner:
    name = "my-planner.v1"

    def solve(self, problem: PlannerInput) -> PlannerResult:
        return PlannerResult(
            verb="act",
            confidence=0.88,
            reason_code="my_choice",
            rationale="the optimal solver chose the valve",
            action_id="valve",
            score=0.91,
        )

decision = PlannerPolicy(MyPlanner()).decide(request)[0]
```

The adapter owns the mapping from the external output to the `PlannerResult` fields. The policy owns the
conversion to `Decision`.

## Simulator

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

## Design rules

1. A planner scores the options the host offers.
2. A planner returns one `PlannerResult` and the same shape as every other planner.
3. A planner is deterministic unless the host supplies a model or a random source.
4. Hard limits gate the choice. A planner may also block on its own concern.
5. A planner result is explainable: chosen option, alternatives, score and reason.
6. `LiveCompositePlanner` composes planners; it does not replace them.
7. A planner can be replaced without changing the request or the response handling.

## Where the code lives

| Path | Contents |
|---|---|
| `core/engines/contract/planner_input.py` | `PlannerInput` |
| `core/engines/contract/planner_result.py` | `PlannerResult` |
| `core/engines/contract/planner.py` | `Planner` |
| `core/engines/contract/planner_policy.py` | `PlannerPolicy`, `to_planner_input`, `to_decision` |
| `core/engines/simulation/` | simulator, scenarios and report |
| `core/engines/planners/` | the six built-in planners |
| `core/engines/live/` | the composite planner |

## Related

- [Policies](../02-decide/03-policies.md) — `PlannerPolicy` as a policy.
- [Live planners](02-live-planners.md) — the four live planners.
- [Live composite planner](03-live-composite-planner.md) — composition.
- [Model-based planners](04-model-based-planners.md) — MDP and POMDP.
