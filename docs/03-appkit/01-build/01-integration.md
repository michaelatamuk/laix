# Integration

The app sends a request. LAIX returns a decision. The app runs the chosen option.

| Word | Meaning |
|---|---|
| **Request** | The app's description of what is happening. |
| **Decision** | LAIX's answer: one verb plus reasons and execution details. |
| **Verb** | The word that says what to do. |
| **Adapter** | App code that builds requests and turns decisions into app actions. |

Start with [the quickstart](../../01-start/02-first-steps/01-quickstart.md) to install LAIX.

## The adapter

The adapter does two things:

1. Turn the app's event into a `DecisionRequest`.
2. Turn the returned `Decision` into an app step.

| Direction | The app owns | LAIX owns |
|---|---|---|
| Input | event, ids, time, context, options, constraints | selection, reason code, score, confidence |
| Output | approval UI, execution, records, delivery | verb, rationale, action, trace id |

The adapter stays in the app. LAIX does not read the app's database, call its transport or run its
skills.

## Build the request

A signal request asks what deserves attention:

```python
from laix import SignalContext, DecisionRequest, DecisionClient, Signal

decision = DecisionClient().decide(
    DecisionRequest(
        subject="one decision",
        at=now,
        signals=(
            Signal(id="s-1", kind="deadline", severity="high", confidence=0.9),
        ),
        context=SignalContext(now=now, quiet_hours=("22:00", "06:00")),
    )
)[0]
```

An option request asks what to do:

```python
from laix import ActionOption, Belief, DecisionRequest, DecisionClient, Situation

decision = DecisionClient().decide(
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
            ActionOption(id="a-wait", verb="wait", name="keep observing", expected_benefit=0.2),
            ActionOption(id="a-act", verb="act", name="apply change", expected_benefit=0.9),
        ),
    )
)[0]
```

TypeScript uses the same shapes:

```ts
import { DecisionClient } from "laix";

const [decision] = new DecisionClient().decide({
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "deadline", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: ["22:00", "06:00"] },
});
```

The request shape is defined in [the decision contract](../../02-core/01-contract/01-decision-contract.md).

## Read the decision

The adapter branches on fields, not on prose:

| Field | Use |
|---|---|
| `verb` | The app step: wait, observe, guide, ask, act, verify or escalate. |
| `reason_code` | Stable branch key; do not parse `rationale`. |
| `action_id` | The option the app should run. |
| `requires_approval` | Pause and ask before executing. |
| `confidence` | How sure the decision is, with its source. |
| `trace_id` | The handle for the decision trail. |
| `deliver` / `record` | Whether to deliver or record the decision. |

## Host confidence

If the host calculates confidence, pass it in:

```python
DecisionRequest(
    ...,
    confidence=0.88,
    confidence_source="host-calibrated",
    calibrated=True,
)
```

The returned decision carries the same source and calibration flag. A rule score stays a rule score.

## Roll out safely

1. Add the adapter behind a flag.
2. Run the old and new paths together.
3. Record both decisions.
4. Compare verb, reason, approval and delivery.
5. Explain each difference.
6. Move traffic to LAIX.
7. Remove the old path after a quiet period.

The production adapter stays in the app. `examples/python/05-execute/host_adapter.py` shows a
generic adapter.

## Manager boundary

A manager service keeps memory and long-lived plans. LAIX returns the decision for the moment.

```text
manager: memory, plans, commitments, missions
LAIX:    whether to act now, how, with what approval, and whether it worked
```

## Privacy

Keep secrets and raw customer data in the host. Pass references where possible. `GroupPolicy` masks
configured fields before sharing; see [privacy](../../04-concepts/03-trust/02-privacy.md).

## Boundary

- The adapter owns the mapping between app events and `DecisionRequest`.
- The adapter owns execution, approval UI, credentials and transport.
- LAIX owns the decision, its reason code, its score and its trace.
- A policy choice is an app decision; see [Policies in the app](03-policies-in-the-app.md).

## Related

- [Single decision](02-single-decision.md) - `DecisionClient` and the one-shot surface.
- [Policies in the app](03-policies-in-the-app.md) - selection, registration and rollout.
- [Streaming](../02-run/02-streaming.md) - decisions over time.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - the write boundary.
