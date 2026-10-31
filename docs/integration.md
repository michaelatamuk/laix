# Integrating LAIX

An app calls LAIX. LAIX returns a decision. The app performs the action. The adapter is the only
place that knows the app.

## 1. Install the package

### Python

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.1.0#subdirectory=python/laix"
```

For local development:

```powershell
pip install -e C:\Workspace\laix\python\laix
```

### TypeScript

For local development, point the app at the package:

```json
{
  "dependencies": {
    "laix": "file:../../laix/typescript/laix"
  }
}
```

The npm package is not published yet. Use a Git checkout or a packed tarball until it is.

## 2. Build the adapter

The adapter has two jobs:

1. Translate the app's event into a `DecisionRequest`.
2. Translate the `Decision` back into an app action.

The adapter keeps the app's nouns. LAIX receives only generic fields.

### Attention request

Use this when the app asks: **which signal deserves attention now, and how?**

```python
from laix import Context, DecisionRequest, Layer, Signal

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="one decision",
        at=now,
        signals=(Signal(id="s-1", kind="deadline", severity="high", confidence=0.9),),
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
            beliefs=(Belief(id="b-1", proposition="the condition is real", confidence=0.9),),
            attributes={"urgency": 0.9},
        ),
        options=(
            Action(id="a-wait", verb="wait", name="keep observing", expected_benefit=0.2),
            Action(id="a-act", verb="act", name="apply change", expected_benefit=0.9),
        ),
    )
)[0]
```

## 3. Read the decision

Every decision carries the same fields:

```text
verb  reason_code  rationale  confidence  evidence
requires_approval  score  breakdown  intent  escalation
cost_of_waiting  reversible  undo_hint  trace_id  deliver  record
```

`verb` is one of:

```text
wait  observe  guide  ask  act  verify  escalate
```

The app maps the decision to its own action:

| Verb | App action |
|---|---|
| `wait` | do nothing; keep the item for later |
| `observe` | take a cheap look or fetch a missing reading |
| `guide` | show the item to the user |
| `ask` | ask the user or an approver |
| `act` | run the chosen action |
| `verify` | check an earlier action |
| `escalate` | hand the decision to another person |

Approval is the `requires_approval` flag. The app asks for approval before running an `act`.

## 4. Roll out in shadow mode

Do not replace the old logic on the first day.

1. Add the adapter behind a flag.
2. Run the old and new decision paths together.
3. Record both decisions.
4. Compare verb, reason, approval and delivery.
5. Explain every difference.
6. Move live traffic to LAIX.
7. Remove the old module after a quiet release.

`examples/apps/` contains one caller example for each working app. The production adapter stays in
the app repository.

## 5. Pin a version

Use a tag, not a branch:

```text
v0.1.0
```

A contract change creates a new version. The app upgrades deliberately.

## 6. Use the manager boundary

A manager service with memory and long-lived plans supplies the state and the allowed actions. LAIX
returns the decision for the moment.

```text
manager: memory, plans, commitments, missions
LAIX:    whether to act now, how, with what approval, and whether it worked
```

The manager keeps its memory and missions. LAIX does not store them.

## 7. Add an HTTP service only when needed

The package runs in-process. Add a small HTTP wrapper when a caller cannot run Python or TypeScript
in the same process:

```text
POST /v1/decide
  -> Layer.decide()
  -> Decision
```

The wrapper adds network latency, authentication and deployment work. It is a separate change.

## 8. Release

The repository has CI for every push and pull request. A tag creates a GitHub release with:

- the Python wheel and source archive;
- the npm tarball.

Registry publishing is a separate decision. Until then, install from the tag or the release
artifacts.
