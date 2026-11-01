# Integrating LAIX

An app calls LAIX, receives one decision, and performs the action itself. The adapter is the only
place that knows the app's nouns.

## Install

### Python

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.6.0#subdirectory=packages/python/laix"
```

For local development:

```powershell
pip install -e C:\Workspace\laix\packages\python\laix
```

### TypeScript

Use a local checkout or the release tarball:

```json
{
  "dependencies": {
    "laix": "file:../../laix/packages/typescript/laix"
  }
}
```

The npm package is not published to a registry yet. The release page includes `laix-0.6.0.tgz`.

## Build the adapter

The adapter does two jobs:

1. Translate the app's event into a `DecisionRequest`.
2. Translate the returned `Decision` back into an app action.

The app keeps its nouns; LAIX receives generic fields.

### Attention request

Use this when the app asks: **which signal deserves attention now, and how?**

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

### Action request

Use this when the app asks: **which of the actions I can afford should I take?**

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

The same two request shapes:

```ts
import { Layer } from "laix";

const [decision] = new Layer().decide({
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "deadline", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: ["22:00", "06:00"] },
});
```

## Read the decision

Every decision has the same shape. The fields you usually branch on:

| Field | Use |
|---|---|
| `verb` | what to do: `wait`, `observe`, `guide`, `ask`, `act`, `verify`, `escalate` |
| `reason_code` | why this rule fired; stable for app logic |
| `action_id` | the chosen option, when there is one |
| `requires_approval` | ask a person before executing |
| `deliver` / `record` | show now / keep in history |

The full field list is in [reading a decision](../design/decisions.md).

| Verb | App action |
|---|---|
| `wait` | do nothing; keep the item for later |
| `observe` | take a cheap look or fetch a missing reading |
| `guide` | show the item to the user |
| `ask` | ask the user or an approver |
| `act` | run the chosen action |
| `verify` | check an earlier action |
| `escalate` | hand the decision to another person |

## Roll out in shadow mode

1. Add the adapter behind a flag.
2. Run the old and new decision paths together.
3. Record both decisions.
4. Compare verb, reason, approval and delivery.
5. Explain every difference.
6. Move live traffic to LAIX.
7. Remove the old module after a quiet period.

`examples/apps/` contains one caller example per working app. The production adapter stays in the app
repository.

## Pin a version

Use a tag, not a branch:

```text
v0.6.0
```

A contract change creates a new version. The app upgrades deliberately.

Tags up to `v0.5.2` use `#subdirectory=python/laix`. Tags from `v0.6.0` use
`#subdirectory=packages/python/laix`. A TypeScript file dependency moves from `typescript/laix` to
`packages/typescript/laix`. App imports stay the same.

## Manager boundary

A manager service supplies memory and long-lived plans. LAIX returns the decision for the moment.

```text
manager: memory, plans, commitments, missions
LAIX:    whether to act now, how, with what approval, and whether it worked
```

The manager keeps its memory and missions. LAIX keeps the decision contract.

## Custom policy

A vertical decision style is a policy plugin:

```python
from laix import Layer, LayerDecision

class QualityPolicy:
    name = "quality"
    version = "1.0"

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

For dynamic selection:

```python
layer.register_policy("quality", QualityPolicy())
layer.use_policy("quality")
layer.status()
layer.explain(decision)
```

TypeScript uses the same pattern with `new Layer({ policy })`, `registerPolicy` and `usePolicy`.

## HTTP service

The package runs in-process. Add a small HTTP wrapper when a caller cannot run Python or TypeScript in
the same process:

```text
POST /v1/decide
  -> Layer.decide()
  -> Decision
```

The wrapper adds network latency, authentication and deployment work, so treat it as a separate
change.

## Release

CI runs on every push. A tag creates a GitHub release with:

- the Python wheel and source archive;
- the npm tarball.

Registry publishing is a separate decision. Install from the tag or the release artifacts until then.
