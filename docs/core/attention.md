# Attention

Attention answers one question inside a task:

> Which signal should be shown now, and how?

It is a decision policy like action. It is a **task-level** policy. The host owns global proactivity
and interruption.

## Inputs

| Input | Meaning |
|---|---|
| `signals` | the items that might need attention |
| `context` | time, quiet hours, minimum severity, feedback, budget |
| `signal.severity` | how much the item matters |
| `signal.confidence` | how sure the app is that it is real |
| `signal.due` | the deadline, if any |

## Output

A decision with a verb such as `guide`, `wait`, `observe` or `escalate`.

```python
from laix import Context, DecisionRequest, Layer, Signal
```

`Layer` is in the app kit; a task can also use the attention policy directly.

## Example

```text
guide worth_surfacing 84.0
```

The bill is important, it is daytime, and the user can decide when to pay.

## Scope

- **Task attention:** this page. LAIX decides about the signals the host gives it.
- **Product proactivity:** the host. The host decides whether the product may interrupt the user at
  all, across apps and tasks.

A host that already has a global interruption policy should keep it and use LAIX
only for task-level signal decisions.

## Related

- [Reading a decision](decisions.md)
- [Host integration](../host-integration.md)
