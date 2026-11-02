# Attention

Attention answers one question inside a task:

> Which signal should be shown now, and how?

It is a built-in rule set. It is a **task-level** rule set. The product owns global proactivity
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
from laix.core.engines.attention import Context, decide_attention

decisions = decide_attention(signals, context)
```

## Example

```text
guide worth_surfacing 84.0
```

The bill is important, it is daytime, and the user can decide when to pay.

## Scope

- **Task attention:** this page. LAIX decides about the signals the product gives it.
- **Product proactivity:** the product. The product decides whether it may interrupt the user at
  all, across apps and tasks.

A product that already has a global interruption rule should keep it and use LAIX
only for task-level signal decisions.
