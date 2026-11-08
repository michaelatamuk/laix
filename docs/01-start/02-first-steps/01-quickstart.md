# Quickstart

**LAIX - Live AI Experience - is the live decision runtime for AI agents and automations that act in
the real world.** Install it, send one request and read one decision. Then choose the surface you need.

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.10.0#subdirectory=packages/python/laix"
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

The release page also has a packed `laix-0.10.0.tgz`. See
[versioning](../../05-project/03-release/01-versioning.md) for tags and schema versions.

## One decision

The snippets assume the app has already built `signal`, `situation` and `options`; see
[the decision contract](../../02-core/01-contract/01-decision-contract.md) for their types.

Attention request:

```python
from datetime import datetime, timezone

from laix import SignalContext, DecisionRequest, decide

decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(signal,),
        context=SignalContext(
            now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
            quiet_hours=None,
        ),
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

Both return the same decision shape. With the app kit, `DecisionClient` adds execution, records and delivery:

```python
from laix import DecisionRequest, DecisionClient

decision = DecisionClient().decide(
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
import { DecisionClient } from "laix";

const [decision] = new DecisionClient().decide({
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
| `reason_code` | Why the decision was made. Branch on this, not on `rationale`. |
| `action_id` | Which option was chosen. |
| `requires_approval` | Ask a person first. |
| `confidence` | How sure the decision is, with its source. |
| `deliver` / `record` | Show now / keep it. |

Full fields: [the decision contract](../../02-core/01-contract/01-decision-contract.md).

## What just happened

1. The request shape selected the path: signals and context go to attention; a situation and options
   go to the action policy.
2. LAIX returned one `Decision` with one verb and one stable reason code.
3. The app chooses what to do with it. LAIX did not execute anything.
4. If `requires_approval` is true, the app asks a person before acting.
5. The app records the outcome if it wants the next decision to learn from it.

If the answer is not the one you expected, start with
[troubleshooting](../../05-project/02-quality/02-troubleshooting.md).

## Choose a surface

| You need | Use |
|---|---|
| One answer, no runtime | `decide` |
| One decision plus execution, records and delivery | `DecisionClient` |
| Decisions over time | `DecisionClient().stream` |
| A write boundary with approval and receipts | `ExecutionBridge` |
| An audit record or a proposal | `DecisionRecord`, `Proposal` |

## Next

- Build a production adapter: [integration](../../03-appkit/01-build/01-integration.md).
- Stream events: [streaming](../../03-appkit/02-run/02-streaming.md).
- Execute and recover: [execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md).
- Learn from outcomes: [outcome learning](../../02-core/02-domain/03-outcomes.md).
- Read the full loop: [decision lifecycle](../01-orientation/02-decision-lifecycle.md).
- Runnable examples: [`../../../examples/README.md`](../../../examples/README.md).
