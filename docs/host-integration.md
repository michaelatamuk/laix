# Host integration

This page is for a product team seeing LAIX for the first time. It answers the
six questions a host team usually asks before trying it.

## 1. Where does LAIX plug in?

LAIX is called by a **task**, not by the product's main loop.

```text
product decides a task exists
        │
        ▼
task builds a DecisionRequest
        │
        ▼
LAIX returns one Decision
        │
        ▼
task acts, asks, waits or escalates
```

Runnable example: [`examples/python/host/mission_adapter.py`](../examples/python/host/mission_adapter.py).

It shows:

- the host's task;
- the request it builds;
- the decision;
- the confidence source;
- the decision basis.

## 2. One reasoning path

The host decides **when** to ask LAIX. LAIX never starts work, watches events or
calls itself.

That means a product keeps one orchestrator. LAIX is a tool inside a task, not a
second orchestrator beside the first.

The example above is the whole flow. There is no background loop in LAIX.

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

LAIX does not pretend that a rule score is a calibrated probability. If the host
does not calibrate, the fields stay empty and `calibrated` is false.

## 4. Approval and execution

Approval is a flag on the decision:

```python
decision.requires_approval
```

The host asks a person if the flag is true, then runs the action through its own
execution path. LAIX can provide an execution bridge for a task, but that is part
of the optional app kit.

Runnable example: [`examples/python/host/mission_execution.py`](../examples/python/host/mission_execution.py).

It shows a decision that needs approval, an owner approval, and a receipt.

## 5. Task attention is not product proactivity

LAIX attention answers:

> Which signal in this task should be shown now?

It is not:

> May this product interrupt the user anywhere, at any time?

The product keeps its own proactivity, quiet hours, daily caps and owner
settings. LAIX attention is a reusable task-level policy, not a second global
interruption manager.

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

## What the host always keeps

| Host keeps | LAIX does not |
|---|---|
| Memory and history | remember the user |
| Apps and connectors | read mail or calendars |
| Proactivity and interruption | decide when to disturb the user |
| Permissions and approvals | own the permission model |
| Missions and dispatch | start or manage work |
| App execution policy | decide auto-run vs ask for host commands |
| User interface | show anything |

## Try it

Run the two examples from the repository root:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/python/host/mission_adapter.py
py examples/python/host/mission_execution.py
```
