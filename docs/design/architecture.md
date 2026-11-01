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

## How a policy is chosen

A policy reads a request and returns a decision. `Layer.decide()` chooses one:

- request with `signals` + `context` → the built-in attention policy;
- request with `situation` + `options` → the built-in action policy;
- any other class → pass a pack explicitly with `Layer(policy=...)` or register it.

## The ten decision classes

| # | Class | Input | Policy | Selected by |
|---|---|---|---|---|
| 1 | Attention | `signals` + `context` | built-in attention | `Layer.decide()` |
| 2 | Action | `situation` + `options` | built-in action | `Layer.decide()` |
| 3 | Active perception | `attributes` | `ActivePerceptionPolicy` | `Layer(policy=...)` |
| 4 | Safety-constrained action | `attributes` | `SafetyConstrainedPolicy` | `Layer(policy=...)` |
| 5 | Replanning | `attributes` | `ReplanningPolicy` | `Layer(policy=...)` |
| 6 | Allocation | `attributes` | `AllocationPolicy` | `Layer(policy=...)` |
| 7 | Negotiation | `attributes` | `NegotiationPolicy` | `Layer(policy=...)` |
| 8 | Preference elicitation | `attributes` | `PreferenceElicitationPolicy` | `Layer(policy=...)` |
| 9 | Verification | `attributes` | `VerificationPolicy` | `Layer(policy=...)` |
| 10 | Escalation | `attributes` | `EscalationPolicy` | `Layer(policy=...)` |

There are ten classes. The first two are built into `Layer` because they define the two request
shapes it understands. The other eight are ordinary policy objects that take their inputs from
`DecisionRequest.attributes`.

The split is about selection, not importance. All ten return the same decision shape. See
[policy packs](../guides/policy-packs.md).

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
