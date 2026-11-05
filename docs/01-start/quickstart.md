# Quickstart

**LAIX — Live AI Experience — is the decision layer for live AI experiences.** Install it, send one
request and read one decision. Then choose the surface you need.

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.9.0#subdirectory=packages/python/laix"
```

Local checkout, from the repository root:

```powershell
pip install -e packages/python/laix
```

TypeScript:

```json
{
  "dependencies": {
    "laix": "file:../path/to/laix/packages/typescript/laix"
  }
}
```

The release page also has a packed `laix-0.9.0.tgz`. See
[versioning](../05-project/versioning.md) for tags and schema versions.

## One decision

The snippets assume the app has already built `signal`, `situation` and `options`; see
[the decision contract](../02-core/01-decision-contract.md) for their types.

Attention request:

```python
from laix import Context, DecisionRequest, decide

decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(signal,),
        context=Context(now="2026-11-01T10:00:00+00:00", quiet_hours=None),
    )
)[0]
```

Action request:

```python
from laix import DecisionRequest, decide

decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=options,
    )
)[0]
```

Both return the same decision shape. With the app kit, `Layer` adds execution, records and delivery:

```python
from laix import DecisionRequest, Layer

decision = Layer().decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=options,
    )
)[0]
```

TypeScript:

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
| `verb` | What to do: `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`. |
| `reason_code` | Why the decision was made. |
| `action_id` | Which option was chosen. |
| `requires_approval` | Ask a person first. |
| `deliver` / `record` | Show now / keep it. |

Full fields: [the decision contract](../02-core/01-decision-contract.md).

## Next

- Build a production adapter: [integration](../03-appkit/01-integration.md).
- Stream events: [streaming](../03-appkit/02-streaming.md).
- Execute and recover: [execution](../03-appkit/04-execution.md).
- Learn from outcomes: [outcome learning](../02-core/04-outcome-learning.md).
- Runnable examples: [`../../examples/README.md`](../../examples/README.md).
