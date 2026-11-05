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
```

Receipt statuses: `pending`, `approved`, `executed`, `refused`, `failed`, `cancelled`, `undone`,
`unknown` and `duplicate`.

## Idempotency and unknown outcomes

- A repeated `idempotency_key` returns a `duplicate` receipt instead of running the handler again.
- `mark_unknown` records that the action may have happened; do not retry blindly.
- `reconcile` resolves an unknown outcome with provider evidence.
- `cancel` and `undo` require the right lifecycle state and a registered undo handler.

## Multi-step execution

`run_steps` executes an ordered set of `ExecutionStep`s. When a step fails, completed steps are
compensated in reverse through their custom compensation or the registered undo handler.

```python
from laix import ActionOption, ExecutionBridge, ExecutionStep

result = bridge.run_steps(
    [
        ExecutionStep(ActionOption(id="a1", verb="act", name="reserve")),
        ExecutionStep(ActionOption(id="a2", verb="act", name="charge")),
    ],
    actor="checkout",
)
print(result.completed, result.compensated, result.error)
```

For a non-bridge saga, use `Saga` and `SagaStep` directly.

## Records

`DecisionRecord` is the audit trail around an execution:

```text
draft -> approved -> executed -> undone
draft -> rejected
```

`create_record`, `approve_record`, `reject_record`, `mark_executed`, `undo` and `verify_record`
move it through the lifecycle. `verify_record` checks the fingerprint after each read.

## Examples

- Python: `examples/python/05-execute/execution.py`
- Python: `examples/python/05-execute/execution_saga.py`
- Python: `examples/python/05-execute/record.py`
- TypeScript: `examples/typescript/05-execute/execution.mts`
- TypeScript: `examples/typescript/05-execute/execution_saga.mts`

## Boundary

Approval, execution, verification and outcome recording stay outside the core. The app owns the
handler, the receipt store and the retry decision.
