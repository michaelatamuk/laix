# Host integration

This page is for a team building an AI agent or automation with LAIX. It answers the six questions
a host team usually asks before trying it.

## Where LAIX plugs in

A task calls LAIX:

```text
product decides a task exists
        │
        ▼
task builds a DecisionRequest
        │
        ▼
decide() returns one Decision
        │
        ▼
task acts, asks, waits or escalates
```

The simplest call is core:

```python
from laix import decide

decision = decide(request)[0]
```

If the host also wants the runtime, execution and records, use `DecisionClient` from the app kit. The
examples below use the app kit because they show execution and audit. See
[Integration](../../03-appkit/01-build/01-integration.md).

Runnable example: [`examples/python/05-execute/host_adapter.py`](../../../examples/python/05-execute/host_adapter.py).

It shows:

- the host's task;
- the request it builds;
- the decision;
- the confidence source;
- the decision basis.

## One reasoning path

The host decides **when** to ask LAIX. LAIX answers when called.

That means a product keeps one orchestrator. LAIX is a tool inside a task.

The example above is the whole flow. The host drives the loop.

## Confidence and calibration

The host may calculate confidence. When it does, it passes it in:

```python
DecisionRequest(
    ...,
    confidence=0.88,
    confidence_source="host-calibrated",
    calibrated=True,
)
```

LAIX carries those values on the returned decision:

```python
decision.confidence          # 0.88
decision.confidence_source   # "host-calibrated"
decision.calibrated          # True
```

LAIX reports confidence as given. A rule score stays a rule score. When the host
leaves calibration out, the fields stay empty and `calibrated` is false.

## Approval and execution

Approval is a flag on the decision:

```python
decision.requires_approval
```

The host asks a person if the flag is true, then runs the chosen option through its own
execution path. LAIX can provide an execution bridge for a task, but that is part
of the optional app kit. The bridge also accepts an idempotency key and can mark an
unknown outcome and reconcile it with provider evidence. See
[Execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md).

Runnable example: [`examples/python/05-execute/host_execution.py`](../../../examples/python/05-execute/host_execution.py).

It shows a decision that needs approval, an owner approval, and a receipt.

## Task attention and product proactivity

LAIX attention answers:

> Which signal in this task deserves attention now?

The product answers:

> May this product interrupt the user anywhere, at any time?

The product keeps its own proactivity, quiet hours, daily caps and owner
settings. LAIX attention is a reusable task-level policy.

## Decision basis

A decision carries a portable basis:

```python
decision.basis()
```

It returns entries the host can put in its own audit record:

```python
[
    {"kind": "reason", "ref": "safe_action", "note": "risk is inside the limit"},
    {"kind": "reference", "ref": "sensor-1", "note": "water detected"},
]
```

The host keeps its own record format. LAIX gives it the evidence and the reason. The record and
proposal lifecycles are in
[Proposals and records](../../03-appkit/03-execute/02-proposals-and-records.md).

## Ownership

| Area | Owner |
|---|---|
| Memory and history | host |
| Apps and connectors | host |
| Proactivity and interruption | host |
| Permissions and approvals | host |
| Missions and dispatch | host |
| App execution policy | host |
| User interface | host |
| Decision shape and policies | LAIX |
| Task perception contracts | LAIX |
| DecisionPolicy bench and parity | LAIX |

## Try it

Run the two examples from the repository root:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/python/05-execute/host_adapter.py
py examples/python/05-execute/host_execution.py
```

## Read next

- [Core overview](../../02-core/README.md) - the contract and the mechanisms.
- [App-kit overview](../../03-appkit/README.md) - the optional runtime.
- [Decision lifecycle](../01-orientation/02-decision-lifecycle.md) - what survives between decisions.
- [Scope and boundaries](../../04-concepts/01-architecture/02-scope-and-boundaries.md) - the host boundary.
