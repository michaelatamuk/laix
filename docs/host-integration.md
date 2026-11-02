# Host integration

This page is for a product team seeing LAIX for the first time. It answers the
six questions a host team usually asks before trying it.

## 1. Where does LAIX plug in?

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

If the host also wants the runtime, execution and records, use `Layer` from the app kit. The
examples below use the app kit because they show execution and audit.

Runnable example: [`examples/appkit/runtime/mission_adapter.py`](../examples/appkit/runtime/mission_adapter.py).

It shows:

- the host's task;
- the request it builds;
- the decision;
- the confidence source;
- the decision basis.

## 2. One reasoning path

The host decides **when** to ask LAIX. LAIX answers only when called.

That means a product keeps one orchestrator. LAIX is a tool inside a task.

The example above is the whole flow. The host drives the loop.

## 3. Confidence and calibration

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

## 4. Approval and execution

Approval is a flag on the decision:

```python
decision.requires_approval
```

The host asks a person if the flag is true, then runs the action through its own
execution path. LAIX can provide an execution bridge for a task, but that is part
of the optional app kit.

Runnable example: [`examples/appkit/runtime/mission_execution.py`](../examples/appkit/runtime/mission_execution.py).

It shows a decision that needs approval, an owner approval, and a receipt.

## 5. Task attention and product proactivity

LAIX attention answers:

> Which signal in this task should be shown now?

The product answers:

> May this product interrupt the user anywhere, at any time?

The product keeps its own proactivity, quiet hours, daily caps and owner
settings. LAIX attention is a reusable task-level policy.

## 6. Decision basis

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

The host keeps its own record format. LAIX gives it the evidence and the reason.

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
| Policy bench and parity | LAIX |

## Try it

Run the two examples from the repository root:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/appkit/runtime/mission_adapter.py
py examples/appkit/runtime/mission_execution.py
```
