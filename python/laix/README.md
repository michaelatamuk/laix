# laix (Python)

One package for the LAIX decision layer: contracts, generic policies, runtime, execution, outcomes
and decision records.

The package uses the Python standard library and its own modules. It takes generic inputs and
returns generic decisions.

## The one API

```python
from laix import DecisionRequest, Layer

layer = Layer()
decisions = layer.decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(signal,),
        context=context,
    )
)
```

`DecisionRequest` carries either:

- `signals` and `context` for attention allocation; or
- `situation` and `options` for action selection.

Both return `laix.LayerDecision`, one shape with `verb`, `confidence`, `reason_code`, `rationale`,
`evidence`, `requires_approval`, `score`, `breakdown`, `intent`, `escalation`,
`cost_of_waiting`, `reversible`, `undo_hint`, `trace_id`, `deliver`, `record` and `created_at`.

## Inside the package

| Piece | Role |
|---|---|
| `contracts.py` | versioned records: observation, belief, goal, constraint, action, situation, decision, outcome, receipt, trace |
| `layer.py` | the public `Layer` and the common decision shape |
| `attention/` | attention policy: gates, score, quiet hours, budget, feedback, replay |
| `state.py` | experience state: goals, phase, beliefs, decay, expiry |
| `policy.py` | action-selection policy |
| `execution.py` | approval gate, execute, cancel, undo, receipts |
| `outcome.py` | directed metric ledger |
| `record.py` | decision record lifecycle: draft, approve, reject, execute, undo, verify |
| `resources.py` | cheap/deep call admission under budget |
| `runtime.py` | the action runtime |
| `schema.py` | generated JSON Schema |

## Test

```powershell
py -m pytest -q
```

## Status

The package contains rules. The 2027 figures are goals.
