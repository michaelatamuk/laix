# Architecture

## What LAIX is

LAIX answers one question:

> Given this situation, what should the app do next?

It returns a **decision**. The app runs the action.

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
| Support | `evidence`, `intent` |
| Audit | `decision_id`, `policy_version`, `trace_id`, `deliver`, `record`, `created_at` |

The `verb` is the core answer. The other fields explain it and help the app execute it.

## The seven verbs

A verb is the action word in a decision.

| Verb | Meaning |
|---|---|
| `wait` | Hold for now; keep watching. |
| `observe` | Get more information before deciding. |
| `guide` | Show the situation to a person and let them choose. |
| `ask` | Ask a person or another agent for information or a decision. |
| `act` | Run the chosen action now. |
| `verify` | Check whether an earlier action worked. |
| `escalate` | Hand the decision to a person with more authority. |

A notification is a `guide` decision plus an app delivery channel. Approval is the
`requires_approval` flag on a decision.

## Selecting a policy

A `Layer` has **one active policy** at a time. Every `decide()` call uses that policy until you
change it.

### One policy for the life of the layer

```python
from laix import DecisionRequest, Layer, SafetyConstrainedPolicy

request = DecisionRequest(
    subject="leaking sink",
    at="2026-11-01T10:00:00+00:00",
    attributes={
        "risk_limit": 0.2,
        "options": [
            {"id": "valve", "benefit": 0.9, "risk": 0.1},
            {"id": "hit-pipe", "benefit": 1.0, "risk": 0.9},
        ],
    },
)

layer = Layer(policy=SafetyConstrainedPolicy())
decision = layer.decide(request)[0]   # act safe_action valve
```

`Layer(policy=...)` activates the policy immediately.

### Several policies, choose at runtime

```python
from laix import Layer, ReplanningPolicy, SafetyConstrainedPolicy

layer = Layer()
layer.register_policy("safety", SafetyConstrainedPolicy())  # stores it
layer.register_policy("replan", ReplanningPolicy())         # stores it

layer.use_policy("safety")   # now safety is active
decision = layer.decide(request)[0]

layer.use_policy("replan")   # switch
decision = layer.decide(another_request)[0]
```

`register_policy` adds a policy to the registry. `use_policy` makes one active.

### If no policy is active

```python
layer = Layer()
```

Then `Layer.decide()` uses the request shape:

| Request has | Policy |
|---|---|
| `situation` + `options` | built-in action |
| `signals` + `context` | built-in attention |

To activate a packaged policy, pass it to `Layer` or select it with `use_policy`. Attributes are input to the active policy.

## The ten decision classes

| # | Class | Input | Policy | Selected by |
|---|---|---|---|---|
| 1 | Attention | `signals` + `context` | built-in attention | request shape |
| 2 | Action | `situation` + `options` | built-in action | request shape |
| 3 | Active perception | `attributes` | `ActivePerceptionPolicy` | explicit policy |
| 4 | Safety-constrained action | `attributes` | `SafetyConstrainedPolicy` | explicit policy |
| 5 | Replanning | `attributes` | `ReplanningPolicy` | explicit policy |
| 6 | Allocation | `attributes` | `AllocationPolicy` | explicit policy |
| 7 | Negotiation | `attributes` | `NegotiationPolicy` | explicit policy |
| 8 | Preference elicitation | `attributes` | `PreferenceElicitationPolicy` | explicit policy |
| 9 | Verification | `attributes` | `VerificationPolicy` | explicit policy |
| 10 | Escalation | `attributes` | `EscalationPolicy` | explicit policy |

There are ten classes. The first two are built into `Layer` because they define the two request
shapes it understands. The other eight are ordinary policy objects that take their inputs from
`DecisionRequest.attributes`.

The split is about selection. All ten return the same decision shape. See
[policy packs](core/policy-packs.md).

## Other parts

- **Live Context** is the perception part. A detector looks at events. Cheap detectors run always;
  deep detectors run under a budget. See [live context](appkit/live-context.md).
- **Outcome learning** uses measured outcomes to improve the next choice. See
  [outcome learning](core/outcome-learning.md).
- **LAIX-Bench** runs the same test cases for every class. See [bench](appkit/bench.md).

LAIX is a decision layer. It can host a decision model such as JEV inside a policy. See
[LAIX and decision models](positioning.md).

## Rules

1. App words stay in the app. LAIX words stay generic.
2. Shared rules become policies. App rules stay in the app.
3. Every policy returns the same decision shape.
4. A score belongs to one policy. Scores rank options inside that policy.
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

The next step is a decision-engine core. It is tracked in
[the engine roadmap](core/engine-roadmap.md).

Core vs app kit vs host is defined in [boundaries](boundaries.md).
