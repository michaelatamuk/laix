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

## Growth rules

1. App names live in app adapters. The layer uses generic vocabulary.
2. Shared rules live in generic policies. App rules live in the app.
3. One contract governs every policy. A change to a verb, reason or field is a version change with a
   new vector.
4. A score describes one policy. Each policy keeps its own score and breakdown.
5. The app owns stored state. The layer reads the state the caller supplies.

## Scope

The layer covers decisions, execution records, outcomes and decision records. Perception, storage,
model routing and user interfaces sit around it.
