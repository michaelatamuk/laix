# Integrating LAIX

The app sends a request. LAIX returns a decision. The app performs the action.

| Word | Meaning |
|---|---|
| **Request** | The app's description of what is happening. |
| **Decision** | LAIX's answer: one verb plus reasons and action details. |
| **Verb** | The action word: `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`. |
| **Adapter** | App code that builds requests and turns decisions into app actions. |

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.6.0#subdirectory=packages/python/laix"
```

Local checkout:

```powershell
pip install -e C:\Workspace\laix\packages\python\laix
```

TypeScript:

```json
{
  "dependencies": {
    "laix": "file:../../laix/packages/typescript/laix"
  }
}
```

The release page also has a packed `laix-0.6.0.tgz`.

## Build the adapter

The adapter does two things:

1. Turn the app's event into a `DecisionRequest`.
2. Turn the returned `Decision` into an app action.

### Attention

```python
from laix import Context, DecisionRequest, Layer, Signal

decision = Layer().decide(
    DecisionRequest(
        subject="one decision",
        at=now,
        signals=(
            Signal(id="s-1", kind="deadline", severity="high", confidence=0.9),
        ),
        context=Context(now=now, quiet_hours=("22:00", "06:00")),
    )
)[0]
```

### Action

```python
from laix import Action, Belief, DecisionRequest, Layer, Situation

decision = Layer().decide(
    DecisionRequest(
        subject="one decision",
        at=now,
        situation=Situation(
            id="situation-1",
            at=now,
            subject="one situation",
            beliefs=(
                Belief(id="b-1", proposition="the condition is real", confidence=0.9),
            ),
            attributes={"urgency": 0.9},
        ),
        options=(
            Action(id="a-wait", verb="wait", name="keep observing", expected_benefit=0.2),
            Action(id="a-act", verb="act", name="apply change", expected_benefit=0.9),
        ),
    )
)[0]
```

### TypeScript

```ts
import { Layer } from "laix";

const [decision] = new Layer().decide({
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "deadline", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: ["22:00", "06:00"] },
});
```

## Use the decision

| Field | Use |
|---|---|
| `verb` | What to do. |
| `reason_code` | Why this rule fired. |
| `action_id` | Which option was chosen. |
| `requires_approval` | Ask a person first. |
| `deliver` / `record` | Show now / keep it. |

| Verb | App action |
|---|---|
| `wait` | Do nothing now. |
| `observe` | Get more information. |
| `guide` | Show it to the user. |
| `ask` | Ask a person or agent. |
| `act` | Run the action. |
| `verify` | Check an earlier action. |
| `escalate` | Hand over to someone else. |

Full fields: [reading a decision](../design/decisions.md).

## Roll out safely

1. Add the adapter behind a flag.
2. Run the old and new paths together.
3. Record both decisions.
4. Compare verb, reason, approval and delivery.
5. Explain each difference.
6. Move traffic to LAIX.
7. Remove the old path after a quiet period.

The production adapter stays in the app. `examples/apps/` shows caller examples.

## Pin a version

Use a tag:

```text
v0.6.0
```

The Python subdirectory is `packages/python/laix`. The TypeScript path is
`packages/typescript/laix`. App imports stay the same.

## Custom policy

```python
from laix import Layer, LayerDecision

class QualityPolicy:
    name = "quality"
    version = "0.6.0"

    def decide(self, request):
        return [
            LayerDecision(
                verb="guide",
                confidence=0.8,
                reason_code="policy_rule",
                rationale="open a watch",
            )
        ]

layer = Layer(policy=QualityPolicy())
```

Or select it at runtime:

```python
layer.register_policy("quality", QualityPolicy())
layer.use_policy("quality")
```

TypeScript uses `new Layer({ policy })`, `registerPolicy` and `usePolicy`.

## Manager boundary

A manager service keeps memory and long-lived plans. LAIX returns the decision for the moment.

```text
manager: memory, plans, commitments, missions
LAIX:    whether to act now, how, with what approval, and whether it worked
```
