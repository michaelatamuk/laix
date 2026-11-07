# Decision runtime

`DecisionRuntime` is the app-kit loop behind `Layer`:

```text
observe -> state -> policy -> execution -> outcome
```

It is in-process and dependency-free. Every decision gets a trace, every execution gets a receipt,
and every measured change is recorded against the decision that caused it. A host can persist the
same records in its own database.

## What it wires

| Piece | Default | Role |
|---|---|---|
| State | `ExperienceState` | Goals, phase, beliefs, observations and history. |
| Policy | `ActionPolicy` | The chooser used by `decide`. |
| Bridge | `ExecutionBridge` | Approval, idempotency, actions and receipts. |
| Outcomes | `OutcomeLedger` | Measured results and labels. |
| Resources | `ResourceScheduler` | Budgeted sensing and deep calls. |
| Ids | `new_id` | Decision, trace and receipt identifiers. |

```python
from laix import ActionOption, DecisionRuntime, Observation, Situation

runtime = DecisionRuntime()

runtime.observe(
    Observation(
        id="o-1",
        at="2026-11-01T10:00:00+00:00",
        source="sensor",
        kind="reading",
        confidence=0.8,
        payload={"proposition": "door is open", "confidence": 0.9},
    )
)

decision = runtime.decide(
    Situation(id="s-1", at="2026-11-01T10:00:00+00:00", subject="door"),
    (
        ActionOption(id="close", verb="act", name="close the door", expected_benefit=0.9),
        ActionOption(id="wait", verb="wait", name="keep observing", expected_benefit=0.2),
    ),
)

print(decision.verb, decision.reason_code, decision.action_id)
```

`decide` returns one `Decision`, not a list. Use `Layer` when you want the dispatch rule and the
convenience surface; use `DecisionRuntime` when you want the loop directly.

## Observe

`observe(observation)` stores the observation and updates a belief when the payload names a
proposition:

```python
runtime.observe(observation)
print(runtime.state.confidence())
```

The state fields and the store port are on [Stores](../04-connect/01-stores.md).

## Decide

`decide(situation, options, attributes=...)` runs the policy, records the decision in the state and
starts a trace:

- the decision is stored by id;
- the options are stored by action id;
- the state history records the decision;
- the trace records the situation and the chosen verb.

## Execute

```python
runtime.bridge.register("close", lambda action, context: {"closed": True})

receipt = runtime.execute(
    decision,
    actor="operator",
    idempotency_key="door-1",
)
print(receipt.status)
```

`execute` resolves the action from the decision, calls the bridge and appends an execution event to
the trace. If approval is required and no approver is supplied, the bridge returns a refused receipt
and the trace records `approval.required`.

The full lifecycle, including cancellation, undo, unknown outcomes and reconciliation, is on
[Execution and recovery](../03-execute/01-execution-and-recovery.md).

## Measure

```python
outcome = runtime.measure(
    decision.decision_id,
    metric="door_closed",
    before=0.0,
    after=1.0,
    label="helped",
)
print(outcome.delta, outcome.label)
```

`measure` writes to the outcome ledger and appends `outcome.measured` to the trace. The outcome is
what learning uses; see [Outcome learning](../../02-core/05-learning/01-outcome-learning.md).

## Schedule

`schedule(options, budget=..., uncertainty=...)` takes `SensingOption` values and returns a
`ResourcePlan` from the resource scheduler. It appends the plan to the state history:

```python
plan = runtime.schedule(sensing_options, budget=budget, uncertainty=0.7)
print(plan.allowed, plan.deep_calls, plan.cost)
```

The resource model is in [Resources](../../02-core/02-decide/04-resources.md). `LiveContext` uses the
same scheduler for detectors; see [Live Context](03-live-context.md).

## Inspect

| Method | Returns |
|---|---|
| `trace(decision_id)` | The `Trace` for the decision. |
| `decision(decision_id)` | The stored decision. |
| `action_for(decision)` | The `ActionOption` behind the action id. |
| `receipts()` | Every execution receipt in order. |
| `stats()` | Decision count, verbs, execution statuses, outcome summary and policy version. |

```python
print(runtime.stats())
print(runtime.trace(decision.decision_id).to_dict())
```

## TypeScript

TypeScript exposes the same loop as `DecisionRuntime` with `RuntimeDecision` results and the same
`observe`, `decide`, `execute`, `measure`, `schedule`, `trace`, `decision`, `actionFor`, `receipts`
and `stats` surface.

## Boundary

- The runtime is in-process. The host owns durable storage, process lifetime and scaling.
- The runtime does not deliver messages or open a network connection.
- A cloud service can persist the same records; the contracts do not change.
- `Layer` adds dispatch, policy registration and delivery around the same runtime.

## Related

- [Single decision](../01-build/02-single-decision.md) - the `Layer` surface.
- [Streaming](02-streaming.md) - the event-time loop above the runtime.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - the write boundary.
- [Stores](../04-connect/01-stores.md) - state and outcome persistence.
