# Architecture

## What LAIX is

LAIX answers one question:

> Given this situation, what should the app do next?

It returns a **decision**. It does not run the action; the app does that.

## Terms used in this documentation

| Term | Meaning |
|---|---|
| **Request** | A description of the situation sent to LAIX. |
| **Signal** | One item that might need attention, such as a deadline or a risk. |
| **Situation** | The current state: what is believed, what the goal is, and what actions exist. |
| **Decision** | LAIX's answer: one verb, a reason, and optional action details. |
| **Verb** | The action word in a decision: `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`. |
| **Policy** | A rule set with a `name` and a `decide(request)` method. It turns a request into a decision. |
| **Adapter** | App code that translates app events into requests and decisions into app actions. |
| **Platform** | The software below LAIX that runs skills, approvals, state and events. |
| **Outcome** | A measured result of a decision, such as time saved or a resolved issue. |

## Flow

```text
app
 │  sends a request
 ▼
LAIX
 │  returns a decision
 ▼
app
 │  runs the action
 ▼
receipt / outcome
 │
 ▼
LAIX records it
```

The app owns the experience, storage and channels. The platform owns execution. LAIX owns the
decision and the records around it.

## The decision

A decision always contains:

| Group | Fields |
|---|---|
| What to do | `verb`, `confidence`, `reason_code`, `rationale` |
| What to run | `action_id`, `intent`, `requires_approval`, `reversible`, `undo_hint` |
| Ranking | `score`, `breakdown`, `cost_of_waiting` |
| Support | `evidence`, `escalation` |
| Audit | `decision_id`, `policy_version`, `trace_id`, `deliver`, `record`, `created_at` |

The `verb` is the core answer. The other fields explain it and help the app execute it.

## The seven verbs

A verb is the action word in a decision.

| Verb | Meaning |
|---|---|
| `wait` | Do nothing now; keep watching. |
| `observe` | Get more information before deciding. |
| `guide` | Show the situation to a person and let them choose. |
| `ask` | Ask a person or another agent for information or a decision. |
| `act` | Run the chosen action now. |
| `verify` | Check whether an earlier action worked. |
| `escalate` | Hand the decision to a person with more authority. |

A notification is a `guide` decision plus an app delivery channel. Approval is the
`requires_approval` flag on a decision.

## How a policy chooses

A policy reads a request and returns a decision. LAIX has two built-in policies for two request
shapes:

| Request contains | Question | Built-in policy |
|---|---|---|
| `signals` + `context` | Which signal deserves attention now, and how? | attention |
| `situation` + `options` | Which available action should we take? | action |

`Layer.decide()` reads the request and calls the matching policy.

## Ten decision classes

A decision class is a kind of question. The two policies above cover attention and action. LAIX also
ships eight reference policies for other classes:

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

Together with attention and action, these make ten classes. The reference policies take generic
inputs from `DecisionRequest.attributes`. See [policy packs](../guides/policy-packs.md).

## Other parts

- **Live Context** is the perception part. A detector looks at events. Cheap detectors run always;
  deep detectors run under a budget. See [live context](../guides/live-context.md).
- **Outcome learning** uses measured outcomes to improve the next choice. See
  [outcome learning](../guides/outcome-learning.md).
- **LAIX-Bench** runs the same test cases for every class. See [bench](../guides/bench.md).

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
