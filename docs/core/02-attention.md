# Attention

Attention answers one question inside a task:

> Which signal deserves attention now, and what should the app do with it?

Attention is a built-in rule set at the task level. It decides which of the signals the product
gives it deserves attention; the product decides whether it may interrupt the user at all.

## Inputs

| Input | Meaning |
|---|---|
| `signals` | the items that might need attention |
| `context` | time, quiet hours, minimum severity, feedback, budget |
| `signal.severity` | how much the item matters |
| `signal.confidence` | how sure the app is that it is real |
| `signal.due` | the deadline, if any |

## Output

Attention returns a `Decision` with one of four verbs:

| Verb | When attention returns it | What the app does |
|---|---|---|
| `guide` | the signal is worth surfacing now | show it |
| `wait` | quiet hours, below floor, low confidence, muted, feedback, budget, already sent or kill switch | hold it |
| `act` | `allow_act` is on, the signal carries an intent, and the intent is reversible | run the intent |
| `escalate` | a critical signal passed `escalate_after_hours` | hand it over |

Attention does not return `observe`, `ask` or `verify`.

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
