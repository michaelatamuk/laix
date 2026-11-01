# Architecture

LAIX turns a described situation into one decision. Everything else exists to make that decision
safe, explainable and measurable.

```text
app or platform
      │  DecisionRequest
      ▼
    LAIX Layer
      │  Decision
      ▼
app or platform executes
      │  Receipt / Outcome
      ▼
LAIX records and learns
```

## Who owns what

| Owner | Owns |
|---|---|
| **App** | Domain rules, detectors, transports, user interface, durable storage, app-specific audit fields |
| **Platform** | Running named skills, approvals, session state, event streams, models and hardware |
| **LAIX** | Contracts, decision policies, admission rules, execution state machine, outcome learning, bench and reference runtime |

LAIX never imports an app and never names a model, vendor or domain.

## One decision shape

Every policy returns the same decision. Fields fall into five groups:

| Group | Fields | Meaning |
|---|---|---|
| **Outcome** | `verb`, `confidence`, `reason_code`, `rationale` | what to do, how sure, why |
| **Choice** | `action_id`, `intent`, `requires_approval`, `reversible`, `undo_hint` | what to run and how to undo it |
| **Cost** | `score`, `breakdown`, `cost_of_waiting` | the policy's ranking, never a hidden model score |
| **Evidence** | `evidence`, `escalation` | what supports the decision and who takes over |
| **Audit** | `decision_id`, `policy_version`, `trace_id`, `deliver`, `record`, `created_at` | how to trace and store it |

The full field-by-field explanation is in [decisions.md](decisions.md).

## The seven verbs

| Verb | Meaning |
|---|---|
| `wait` | Do nothing now; keep watching. |
| `observe` | Get more information before deciding. |
| `guide` | Show the situation to a person and let them choose. |
| `ask` | Ask a person or another agent for information or a decision. |
| `act` | Run the chosen action now. |
| `verify` | Check whether an earlier action worked. |
| `escalate` | Hand the decision to a person with more authority. |

There is no `notify` verb. When an app notifies someone, the decision is `guide`; delivery is a
separate concern. Approval is the `requires_approval` flag, not a verb. `verify` is both a verb and a
lifecycle phase, depending on whether it is deciding to check or recording that a check happened.

## Two common requests

| Request | Question | Built-in policy |
|---|---|---|
| `signals` + `context` | Which signal deserves attention now, and how? | attention |
| `situation` + `options` | Which available action should we take? | action |

`Layer.decide()` chooses the right policy from the request shape.

## Ten decision classes

The two request shapes above are the common path. LAIX also ships deterministic reference policies
for the other classes:

| # | Class | Policy |
|---|---|---|
| 1 | Attention | built-in attention policy |
| 2 | Action | built-in action policy |
| 3 | Active perception | `ActivePerceptionPolicy` |
| 4 | Safety-constrained action | `SafetyConstrainedPolicy` |
| 5 | Replanning | `ReplanningPolicy` |
| 6 | Allocation | `AllocationPolicy` |
| 7 | Negotiation | `NegotiationPolicy` |
| 8 | Preference elicitation | `PreferenceElicitationPolicy` |
| 9 | Verification | `VerificationPolicy` |
| 10 | Escalation | `EscalationPolicy` |

The packs read generic inputs from `DecisionRequest.attributes`, return the same decision shape and
are registered like any other policy. They are starting points, not tuned research models. An app
can use one directly, wrap it, or replace it behind the same interface. See
[policy packs](../guides/policy-packs.md).

## Perception, learning and measurement

- **Live Context** runs detectors: cheap ones on every event, deep ones only when their information
  gain, cost and latency clear the budget. Each event produces a perception frame. See
  [live context](../guides/live-context.md).
- **Outcome learning** turns measured outcome labels into rewards and lets `BanditPolicy` change the
  next choice. See [outcome learning](../guides/outcome-learning.md).
- **LAIX-Bench** runs deterministic cases for every decision class and reports agreement per class.
  See [bench](../guides/bench.md).

## Extension points

| Seam | Contract | Role |
|---|---|---|
| Policy | `name`, `decide(request)` | choose a decision |
| Detector | `name`, `tier`, cost/latency/gain, `detect(event)` | produce observations |
| Learned policy | `BanditPolicy` + `UCBBandit` | improve from outcomes |
| Execution bridge | `ExecutionBridge` | approve, run, cancel, undo, receipt |
| Platform | `Platform` | run skills, approve, state, events, capability level |
| Proposal | `Proposal` | an action that needs a person |
| Delivery | `DeliveryPort` | send a decision through an app channel |
| State store | `StateStore` | save and load experience state |
| Outcome store | `OutcomeStore` | record decision consequences |
| Evaluation | `Case`, `compare` | compare policies on the same cases |

## Boundaries

LAIX owns the decision and the records around it. It does not own:

- the app's database or user interface;
- the app's channels or hardware;
- the platform's model routing;
- an edge/cloud runtime split;
- reference apps or a coach.

Those are integrations, not missing decisions.

## Growth rules

1. App nouns stay in app adapters. LAIX uses generic vocabulary.
2. Shared rules become generic policies. App rules stay in the app.
3. Every policy returns the same decision shape. A verb, reason or field change is a version change.
4. A score describes one policy. Each policy keeps its own score and breakdown.
5. The app owns stored state. LAIX defines the contract and reads what the caller supplies.
