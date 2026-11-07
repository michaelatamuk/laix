# Single decision

`DecisionClient` is the one-decision surface of the app kit. It wraps the core, keeps the runtime, and can
execute, measure and deliver the result.

```python
from laix import ActionOption, Constraint, DecisionRequest, DecisionClient, Situation

layer = DecisionClient()

request = DecisionRequest(
    subject="invoice",
    at="2026-11-01T10:00:00+00:00",
    situation=Situation(
        id="situation-1",
        at="2026-11-01T10:00:00+00:00",
        subject="invoice",
        constraints=(Constraint(id="risk", kind="risk", value=0.3, hard=True),),
    ),
    options=(
        ActionOption(id="pay", verb="act", name="pay the invoice", expected_benefit=0.9, risk=0.1),
        ActionOption(id="skip", verb="wait", name="wait", expected_benefit=0.2),
    ),
)

decision = layer.decide(request)[0]
print(decision.verb, decision.reason_code, decision.action_id)
```

The request has a situation and options, so `DecisionClient` selects the action path. The hard risk limit
removes any unsafe option before the choice.

## What `DecisionClient` owns

| Method | Returns | Use |
|---|---|---|
| `decide(request)` | `list[Decision]` | One decision through the core. |
| `stream(**options)` | `StreamSession` | A live loop over many events. |
| `execute(decision, ...)` | `ExecutionReceipt` | Run the chosen action through the runtime bridge. |
| `measure(decision, ...)` | `Outcome` | Record what changed after the action. |
| `deliver(decision, port, message, ...)` | `DeliveryReceipt` | Send the decision through a delivery port. |
| `explain(decision)` | `dict` | The reason, evidence, score, approval and trace in one view. |
| `status()` | `dict` | Schema version, policy, policy version and decision count. |
| `register_policy(name, policy)` | `None` | Add a policy to the layer registry. |
| `use_policy(name)` | `None` | Select a registered policy. |
| `policies()` | `tuple[str, ...]` | List the registered policies. |
| `bridge()` | `ExecutionBridge` | The execution bridge behind the layer. |

`DecisionClient` is a convenience surface, not a second core. The decision contract, the verbs and the reason
codes are the same.

## `DecisionClient` or `decide`

| Surface | What you get | Use it when |
|---|---|---|
| `decide(request)` | The answer only. | You already have execution and records. |
| `DecisionClient().decide(request)` | The answer plus the runtime, policy registry, execution bridge, records and delivery. | You want one object for a complete app step. |

The core entry point is described in [Dispatch](../../02-core/01-contract/03-dispatch.md).

## The response

A `Decision` carries:

- one verb from `wait`, `observe`, `guide`, `ask`, `act`, `verify` and `escalate`;
- a stable `reason_code`;
- a `confidence` and its source;
- an `action_id` when the decision selects an option;
- `requires_approval` when a person must approve before execution;
- a `trace_id`, and optional `deliver` and `record` flags;
- the score and its breakdown when a planner produced it.

The full shape is in [the decision contract](../../02-core/01-contract/01-decision-contract.md).

## Explain and status

```python
print(layer.explain(decision))
print(layer.status())
```

`explain()` returns the verb, reason code, rationale, confidence, evidence, score, breakdown,
approval flag, delivery flag, record flag and trace id. `status()` returns the schema version, the
selected policy, the policy version, the number of decisions and the registered policy names.

## Execute, measure and deliver

The layer can run the action through the runtime bridge:

```python
layer.bridge().register("pay", lambda action, context: {"paid": True})

receipt = layer.execute(decision, actor="operator", idempotency_key="invoice-1")
outcome = layer.measure(decision, metric="paid", before=0.0, after=1.0)
```

The bridge checks approval, enforces idempotency and records a receipt. The outcome is stored against
the decision. The [execution page](../03-execute/01-execution-and-recovery.md) covers the lifecycle
and recovery.

Delivery is a port:

```python
from laix import NullDelivery

receipt = layer.deliver(decision, NullDelivery(), "the decision", channel="email")
print(receipt.status)
```

The host owns the transport. The [delivery page](../04-connect/03-delivery.md) covers the port and
the receipt.

## TypeScript

```ts
import { DecisionClient } from "laix";

const layer = new DecisionClient();
const [decision] = layer.decide({
  subject: "invoice",
  at: "2026-11-01T10:00:00Z",
  situation: { id: "situation-1", at: "2026-11-01T10:00:00Z", subject: "invoice" },
  options: [{ id: "pay", verb: "act", name: "pay the invoice", expectedBenefit: 0.9 }],
});
```

TypeScript exposes the same `decide`, `stream`, `execute`, `measure`, `deliver`, `explain`,
`status`, `registerPolicy`, `usePolicy` and `policies` surface. The request input types are
`CreateDecisionInput` and `CreateOptions`; `decideAction` applies the built-in action policy.

## Boundary

`DecisionClient.decide` evaluates one request. It does not keep an event-time watermark or a stream buffer;
use [Streaming](../02-run/02-streaming.md) for that. It does not choose the policy for you beyond the
built-in dispatch rule; use [Policies in the app](03-policies-in-the-app.md) for selection and rollout.

## Related

- [Integration](01-integration.md) - the adapter around the call.
- [Policies in the app](03-policies-in-the-app.md) - the policy registry and rollout.
- [Decision runtime](../02-run/01-decision-runtime.md) - the loop behind `DecisionClient`.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - the write boundary.
