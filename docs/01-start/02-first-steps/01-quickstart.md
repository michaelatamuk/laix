# Quickstart

**LAIX - Live AI Experience - is the live decision layer for AI agents that act in
the real world.** Install it, send one request and read one decision. Then choose the surface you need.

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.13.0#subdirectory=packages/python/laix"
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

The release page also has a packed `laix-0.13.0.tgz`. See
[versioning](../../05-project/03-release/01-versioning.md) for tags and schema versions.

## One decision

The snippets assume the app has already built `signal`, `situation` and `options`; see
[the decision contract](../../02-decision/01-contract/01-decision-contract.md) for their types.

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

Full fields: [the decision contract](../../02-decision/01-contract/01-decision-contract.md).

## What just happened

1. The request shape selected the path: signals and context go to attention; a situation and options
   go to the action policy.
2. LAIX returned one `Decision` with one verb and one stable reason code.
3. The app chooses what to do with it. LAIX did not execute anything.
4. If `requires_approval` is true, the app asks a person before acting.
5. The app records the outcome if it wants the next decision to learn from it.

If the answer is not the one you expected, start with
[troubleshooting](../../05-project/02-quality/02-troubleshooting.md).

## Full request: approval, commitment and attention

This request carries a payment, a promise and a human-attention budget. The default action policy
selects `pay` and flags the approval.

```python
import json

from laix import (
    ActionOption,
    Belief,
    Commitment,
    DecisionRequest,
    HumanAttentionBudget,
    Situation,
    decide,
)

request = DecisionRequest(
    subject="invoice 4832",
    at="2026-11-01T10:00:00+00:00",
    situation=Situation(
        id="s-1",
        at="2026-11-01T10:00:00+00:00",
        subject="invoice 4832",
        beliefs=(
            Belief(
                id="b-1",
                proposition="the invoice matches the work order",
                confidence=0.95,
            ),
        ),
        attributes={"urgency": 0.8},
    ),
    options=(
        ActionOption(
            id="pay",
            verb="act",
            name="pay the invoice",
            expected_benefit=0.95,
            risk=0.05,
            requires_approval=True,
            reversible=False,
            interrupt_cost=0.6,
            params={"commitments": {"violates": ["c1"]}},  # pays without asking
        ),
        ActionOption(
            id="ask",
            verb="ask",
            name="ask the owner for approval",
            expected_benefit=0.6,
            interrupt_cost=0.2,
            params={"commitments": {"fulfills": ["c1"]}},  # asks before paying
        ),
        ActionOption(
            id="wait",
            verb="wait",
            name="wait for the next review",
            expected_benefit=0.2,
            interrupt_cost=0.0,
        ),
    ),
    attributes={
        "commitments": (
            Commitment(
                id="c1",
                subject="ask the owner before paying",
                due="2026-11-01T09:00:00+00:00",
            ),
        ),
        "human_attention_budget": HumanAttentionBudget(total=2.0, spent=0.5),
    },
)

decision = decide(request)[0]

print(json.dumps({
    "verb": decision.verb,
    "reason_code": decision.reason_code,
    "action_id": decision.action_id,
    "confidence": decision.confidence,
    "score": decision.score,
    "requires_approval": decision.requires_approval,
    "reversible": decision.reversible,
    "decision_id": decision.decision_id,
    "trace_id": decision.trace_id,
}, indent=2))
```

```text
{
  "verb": "act",
  "reason_code": "policy_rule",
  "action_id": "pay",
  "confidence": 0.95,
  "score": 0.8475,
  "requires_approval": true,
  "reversible": false,
  "decision_id": "DEC-...",
  "trace_id": "TRC-..."
}
```

The default action policy uses one utility score and the approval flag; it does not weigh the promise
or the attention budget separately.

The same request with the composite planner:

```python
import json

from laix import LiveCompositePlanner, PlannerPolicy, decide

policy = PlannerPolicy(LiveCompositePlanner(), name="live.v1")
decision = decide(request, policy=policy)[0]

print(decision.action_id, decision.reason_code, decision.score)
print(json.dumps({
    "utility": decision.attributes["utility"],
    "commitment": decision.attributes["commitment_score"],
    "execution": decision.attributes["execution_score"],
    "human_attention": decision.attributes["human_attention_score"],
}, indent=2))
```

```text
ask live_decision 1.09
{
  "utility": 0.57,
  "commitment": 0.6,
  "execution": -0.0,
  "human_attention": -0.08
}
```

The composite planner chooses `ask` over `pay`. `pay` has the higher utility, but it breaks the
commitment to ask the owner before paying; `ask` fulfills that commitment and stays within the
human-attention budget. The decision carries the four scores, so the trade-off is visible.

## Choose a surface

| You need | Use |
|---|---|
| One answer, no loop | `decide` |
| One decision plus execution, records and delivery | `DecisionClient` |
| Decisions over time | `DecisionClient().stream` |
| A write boundary with approval and receipts | `ExecutionBridge` |
| An audit record or a proposal | `DecisionRecord`, `Proposal` |

## Next

- Build a production adapter: [integration](../../03-appkit/01-build/01-integration.md).
- Stream events: [streaming](../../03-appkit/02-run/02-streaming.md).
- Execute and recover: [execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md).
- Learn from outcomes: [outcome learning](../../02-decision/02-domain/03-outcomes.md).
- Read the full loop: [decision lifecycle](../01-orientation/02-decision-lifecycle.md).
- Runnable examples: [`../../../examples/README.md`](../../../examples/README.md).
