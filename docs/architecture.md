# Design

## The shape

```
app -> one request -> LAIX Layer -> one Decision -> app executes
                                      |
                                receipt / outcome / record
```

The app supplies the situation and its limits. LAIX returns a decision. The app, or the platform
under it, performs the action. LAIX records the result.

## One decision shape

Every policy returns the same fields:

`verb`, `confidence`, `reason_code`, `rationale`, `evidence`, `requires_approval`, `score`,
`breakdown`, `intent`, `escalation`, `cost_of_waiting`, `reversible`, `undo_hint`, `trace_id`,
`deliver`, `record`, `created_at`.

`verb` is one of `wait`, `observe`, `guide`, `ask`, `act`, `verify`, `escalate`. `notify` is the
delivery form of `guide`. Approval is the `requires_approval` flag on the decision; `verify` is a
lifecycle phase after an action.

## Two generic requests

| Request | Question | Policy |
|---|---|---|
| signals + context | Which signal deserves attention now, and how? | attention |
| situation + options | Which available action should we take? | action |

The app sends one request. `Layer.decide()` reads it and uses the matching generic policy.

## Reference policy packs

The two request shapes above are the common path. LAIX also ships deterministic reference policies
for other decision classes: active perception, safety-constrained action, replanning, allocation,
negotiation, preference elicitation, verification and escalation. With attention and action, the
layer covers ten decision classes. They read generic inputs from `DecisionRequest.attributes`,
return the same decision shape, and are registered like any other policy. An app can use a pack
directly or replace it with a learned policy behind the same interface. `docs/policy-packs.md`
describes each contract.

## Growth rules

1. App names live in app adapters. The layer uses generic vocabulary.
2. Shared rules live in generic policies. App rules live in the app.
3. One contract governs every policy. A change to a verb, reason or field is a version change with a
   new vector.
4. A score describes one policy. Each policy keeps its own score and breakdown.
5. The app owns stored state. The layer reads the state the caller supplies.

## Extension points

The layer has four generic seams:

- **Policy plugin** — any object with `name` and `decide(request)`; register it with
  `Layer.register_policy()` and select it with `use_policy()`.
- **Detector** — any object with `name`, `tier`, `cost`, `latency_ms`, `information_gain` and
  `detect(event)`; `LiveContext` admits cheap detectors always and deep ones under budget.
- **Learned policy** — `BanditPolicy` chooses among arms from `UCBBandit` and improves from measured
  outcome labels.
- **Platform interface** — run a named skill, cancel, approve, read/write state, stream events and
  request a capability level.
- **Proposal** — a storage-free record for an action that needs a person: pending, approved,
  rejected, applied, undone.
- **Delivery port** — the app supplies the transport; the layer supplies the decision and expects a
  delivery receipt.
- **State store** — save, load and delete experience snapshots.
- **Outcome store** — record decision consequences and return a summary.
- **Parity harness** — compare two policies or two versions of one policy on the same cases.

These are contracts. The app keeps its database, channels, UI and domain rules.

## Scope

The layer covers decisions, execution records, outcomes and decision records. Perception, storage,
model routing and user interfaces sit around it.
