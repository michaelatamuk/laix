# Architecture

LAIX takes a description of a situation and returns one decision. The app or platform then executes
that decision.

```text
app
 │  DecisionRequest
 ▼
LAIX
 │  Decision
 ▼
app executes
 │  Receipt / Outcome
 ▼
LAIX records it
```

## Who does what

| Part | Job |
|---|---|
| App | Describes the situation, executes the action, owns storage and UI |
| LAIX | Chooses the verb, explains it, records it, measures it |
| Platform | Runs skills, approvals, state and events |

LAIX uses generic words. App names, domains and vendor names stay outside it.

## A decision

Every policy returns the same fields:

| Group | Fields |
|---|---|
| What | `verb`, `confidence`, `reason_code`, `rationale` |
| Action | `action_id`, `intent`, `requires_approval`, `reversible`, `undo_hint` |
| Cost | `score`, `breakdown`, `cost_of_waiting` |
| Evidence | `evidence`, `escalation` |
| Audit | `decision_id`, `policy_version`, `trace_id`, `deliver`, `record`, `created_at` |

The seven verbs are `wait`, `observe`, `guide`, `ask`, `act`, `verify` and `escalate`.

Delivery is separate. When an app notifies someone, the decision verb is `guide` and the app chooses
the channel. `verify` is a verb when LAIX chooses to check, and a lifecycle phase when a check is due
or finished.

## Requests and decision classes

Two request shapes cover the common cases:

| Request | Question |
|---|---|
| `signals` + `context` | Which signal deserves attention now, and how? |
| `situation` + `options` | Which available action should we take? |

LAIX also has eight reference policies for other decision classes:

| Class | Policy |
|---|---|
| Active perception | `ActivePerceptionPolicy` |
| Safety-constrained action | `SafetyConstrainedPolicy` |
| Replanning | `ReplanningPolicy` |
| Allocation | `AllocationPolicy` |
| Negotiation | `NegotiationPolicy` |
| Preference elicitation | `PreferenceElicitationPolicy` |
| Verification | `VerificationPolicy` |
| Escalation | `EscalationPolicy` |

With attention and action, that makes ten classes. The packs take generic inputs from
`DecisionRequest.attributes` and return the same decision shape. See
[policy packs](../guides/policy-packs.md).

## Other parts

- **Live Context** runs cheap detectors always and deep detectors under a budget. See
  [live context](../guides/live-context.md).
- **Outcome learning** turns measured outcomes into rewards and improves the next choice. See
  [outcome learning](../guides/outcome-learning.md).
- **LAIX-Bench** runs the same cases for every class. See [bench](../guides/bench.md).

## Rules

1. App words stay in the app. LAIX words stay generic.
2. Shared rules become policies. App rules stay in the app.
3. Every policy returns the same decision shape.
4. A score belongs to one policy. Do not compare scores across policies.
5. The app stores its own data. LAIX defines the contracts.

## Extend it

| Need | Use |
|---|---|
| New decision rules | A policy with `name` and `decide(request)` |
| New perception | A detector with `detect(event)` |
| New learning | A policy backed by `UCBBandit` or another learner |
| New execution | `ExecutionBridge` or a `Platform` |
| New storage | Implement `StateStore` or `OutcomeStore` |
| New channel | Implement `DeliveryPort` |
