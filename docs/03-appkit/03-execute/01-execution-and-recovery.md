# Execution and recovery

LAIX decides. The host executes. The app kit supplies the boundary around that write.

## Execution bridge

`ExecutionBridge` runs a named host skill for a chosen action and records an `ExecutionReceipt`.

```python
from laix import ActionOption, Decision, ExecutionBridge

bridge = ExecutionBridge(handlers={"close": lambda action, context: {"closed": True}})
receipt = bridge.execute(
    decision,
    action=action,
    actor="operator",
    idempotency_key="case-1",
)
print(receipt.status)
```

The bridge owns the lifecycle around the handler. It does not own the handler itself, the
credentials or the external system.

## Receipt statuses

| Status | Meaning |
|---|---|
| `pending` | The action is waiting for approval or execution. |
| `approved` | A person approved it; it is ready to run. |
| `executed` | The handler ran and returned a result. |
| `refused` | The bridge refused the action, usually because approval is missing. |
| `failed` | The handler raised or returned a failure. |
| `cancelled` | The action was cancelled before completion. |
| `undone` | The action was reversed. |
| `unknown` | The action may have happened; provider evidence is needed. |
| `duplicate` | The idempotency key was already used; the original receipt is returned. |

`ApprovalRequired` is raised when an action needs approval and no approver is supplied.
`UnknownAction` is raised when no handler is registered for the action.

## Idempotency and unknown outcomes

- A repeated `idempotency_key` returns a `duplicate` receipt.
- `mark_unknown` records that the action may have happened.
- `reconcile` resolves an unknown outcome with provider evidence before a retry.
- `cancel` and `undo` require the right lifecycle state and a registered undo handler.

```python
receipt = bridge.mark_unknown(receipt.id, actor="operator", reason="provider timeout")
receipt = bridge.reconcile(
    receipt.id,
    actor="operator",
    status="executed",
    detail={"provider_id": "ch-1"},
)
```

Retry at the host, not inside the decision. Retrying `decide` is safe; retrying an effect is safe
only with an idempotency key.

## Multi-step execution

A **saga** is a multi-step action where each step has a way to undo itself. Steps run in order. If a
later step fails, the completed steps are compensated in reverse, so the world returns to a
consistent state.

Example: book a flight, then a hotel, then a car. If the car fails, cancel the hotel, then cancel the
flight.

```python
from laix import Saga, SagaStep

result = Saga().run(
    [
        SagaStep("book_flight", forward=book_flight, compensate=cancel_flight),
        SagaStep("book_hotel", forward=book_hotel, compensate=cancel_hotel),
        SagaStep("book_car", forward=book_car, compensate=cancel_car),
    ]
)

print(result.completed)     # steps that succeeded
print(result.compensated)   # steps that were undone
print(result.error)         # None when every step succeeded
```

`SagaResult` carries `completed`, `compensated` and `error`. Compensation is best effort: one failing
compensation leaves the others to run.

`ExecutionBridge.run_steps` applies the same idea to execution steps and returns an
`ExecutionSagaResult` with every receipt:

```python
from laix import ActionOption, ExecutionBridge, ExecutionStep

bridge = ExecutionBridge(handlers={"reserve": reserve, "charge": charge})
result = bridge.run_steps(
    [
        ExecutionStep(ActionOption(id="a1", verb="act", name="reserve")),
        ExecutionStep(ActionOption(id="a2", verb="act", name="charge")),
    ],
    actor="checkout",
)
print(result.completed, result.compensated, result.receipts, result.error)
```

Each `ExecutionStep` can carry its own `decision`, `actor`, `approver`, `context`,
`idempotency_key` and `compensate` callback.

## Records

`DecisionRecord` is the audit trail around an execution:

```text
draft -> approved -> executed -> undone
draft -> rejected
```

`create_record`, `approve_record`, `reject_record`, `mark_executed`, `undo` and `verify_record` move
it through the lifecycle. `verify_record` checks the fingerprint after each read. The record and
proposal lifecycles are on [Proposals and records](02-proposals-and-records.md).

## Failure modes

- **Approval missing** - the bridge returns `refused`; ask the person and retry.
- **Duplicate key** - the original receipt is returned; do not run the effect twice.
- **Unknown outcome** - mark it unknown, reconcile with provider evidence, then decide.
- **Partial failure** - compensate completed steps in reverse and report what was compensated.
- **Compensation failure** - report it; do not pretend the world is consistent.

## Examples

- Python: `examples/python/appkit/execute/execution.py`
- Python: `examples/python/appkit/execute/execution_saga.py`
- Python: `examples/python/appkit/execute/saga.py`
- Python: `examples/python/appkit/execute/record.py`
- TypeScript: `examples/typescript/appkit/execute/execution.mts`
- TypeScript: `examples/typescript/appkit/execute/execution_saga.mts`

## TypeScript

TypeScript exposes the same bridge and saga surface with `Handler`, `SagaForward` and
`SagaCompensate` function types.

## Boundary

Approval, execution, verification and outcome recording stay outside the core. The app owns the
handler, the receipt store and the retry decision. The bridge defines the lifecycle and the receipt
shape; it does not open a network connection or hold credentials.

## Related

- [Proposals and records](02-proposals-and-records.md) - approval and audit lifecycles.
- [Platform](../04-connect/02-platform.md) - skills, approvals and events.
- [Stores](../04-connect/01-stores.md) - receipts and state persistence.
- [Deployment](../05-operate/03-deployment.md) - reliability and rollout.
