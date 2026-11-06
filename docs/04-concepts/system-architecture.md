# System architecture

## What LAIX is

**LAIX — Live AI Experience — is the decision layer for live AI experiences.** It answers one
question:

> Given this situation, what should the experience do next?

It returns a **decision**. The app runs the chosen option.

## Terms

The vocabulary is defined once in the [glossary](glossary.md).

## Flow

```text
app
 │  sends a request
 ▼
LAIX
 │  returns a decision
 ▼
app
 │  runs the chosen option
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

## Getting a decision

For the answer alone, use the core:

```python
from laix import decide

decision = decide(request)[0]
```

For the answer plus the runtime, traces, execution and records, use the app kit:

```python
from laix import Layer

layer = Layer()
decision = layer.decide(request)[0]
```

`decide` lives in core and loads without the app kit. `Layer` uses the same core selection and
adds the app-kit parts.

## The seven verbs

A verb is the word that says what to do in a decision.

| Verb | Meaning |
|---|---|
| `wait` | Hold for now; keep watching. |
| `observe` | Get more information before deciding. |
| `guide` | Show the situation to a person and let them choose. |
| `ask` | Ask a person or another agent for information or a decision. |
| `act` | Run the chosen option now. |
| `verify` | Check whether an earlier step worked. |
| `escalate` | Hand the decision to a person with more authority. |

A notification is a `guide` decision plus an app delivery channel. Approval is the
`requires_approval` flag on a decision.

## Selecting a policy

Pass a policy explicitly to the core:

```python
from laix import DecisionRequest, SafetyConstrainedPolicy, decide

decision = decide(request, policy=SafetyConstrainedPolicy())[0]
```

In the app kit, a `Layer` holds **one active policy** at a time. Every `decide()` call uses that
policy until you change it.

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

### The default policy

```python
decision = decide(request)[0]
```

or, with the app kit:

```python
layer = Layer()
decision = layer.decide(request)[0]
```

Selection then uses the request shape:

| Request has | Path |
|---|---|
| `situation` + `options` | built-in action policy |
| `signals` + `context` | built-in attention |

To use a packaged policy, pass it to `decide` or to `Layer`, or select it with `use_policy`.
Attributes are input to the active policy.

## The ten decision classes

| # | Class | Input | Policy | Selected by |
|---|---|---|---|---|
| 1 | Attention | `signals` + `context` | built-in attention | request shape |
| 2 | Action decision | `situation` + `options` | built-in action policy | request shape |
| 3 | Active perception | `attributes` | `ActivePerceptionPolicy` | explicit policy |
| 4 | Safety-constrained action | `attributes` | `SafetyConstrainedPolicy` | explicit policy |
| 5 | Replanning | `attributes` | `ReplanningPolicy` | explicit policy |
| 6 | Allocation | `attributes` | `AllocationPolicy` | explicit policy |
| 7 | Negotiation | `attributes` | `NegotiationPolicy` | explicit policy |
| 8 | Preference elicitation | `attributes` | `PreferenceElicitationPolicy` | explicit policy |
| 9 | Verification | `attributes` | `VerificationPolicy` | explicit policy |
| 10 | Escalation | `attributes` | `EscalationPolicy` | explicit policy |

There are ten classes. The first two are built into `decide` and `Layer` because they define the two
request shapes LAIX understands. The other eight are ordinary policy objects that take their inputs
from `DecisionRequest.attributes`.

The split is about selection. All ten return the same decision shape. See
[packaged policies](../02-core/03-policies.md).

## Other parts

- **Live Context** is the perception part. A detector looks at events. Cheap detectors run always;
  deep detectors run under a budget. See [live context](../03-appkit/03-live-context.md).
- **Outcome learning** uses measured outcomes to improve the next choice. See
  [outcome learning](../02-core/04-outcome-learning.md).
- **LAIX-Bench** runs the same test cases for every class. See [bench](../03-appkit/08-laix-bench.md).

LAIX is a decision layer. It can host a decision model such as JEV inside a policy. See
[LAIX and decision models](decision-models.md).

## Integration evidence

The integration is not asserted — it is measured. `LiveDecisionEngine` runs every concern in one
score. Single-concern planners win their own cases; `live` wins every case because it integrates
all three.

**Live bench (7 cases, all planners):**

| Planner | Correct / 7 | Note |
|---|---:|---|
| `benefit` (naive) | 1 / 7 | ignores risk, commitments, attention |
| `utility` | 2 / 7 | ignores commitments and attention |
| `commitment` | 3 / 7 | ignores execution risk and attention |
| `attention` | 4 / 7 | ignores commitments and execution risk |
| `execution` | 5 / 7 | ignores commitments and attention |
| **`live`** | **7 / 7** | integrates all three concerns |

Reproduce with one command: `python examples/python/03-plan/ablation_study.py`.

A worked conflict scenario (all three concerns fire simultaneously) is in
`examples/python/03-plan/conflict_scenario.py`.

**Expanded corpus:** 120 cases across six categories (72 dev, 30 test, 18 adversarial).
On the frozen test split, the integrated planner is 30/30 and wins every conflict case (6/6).
A hand-built glue baseline reaches 28/30 (93.3%), so the remaining integration advantage is
+6.7 pp and is not significant on 30 cases. Ablations on the same split: full 100%, no attention
96.7%, no feasibility gates 93.3%, no execution 83.3%, no commitment 70%, utility-only 30%.
Reproduce with `bash scripts/novelty/reproduce.sh`.

**Prior art:** No compared system (LangGraph, Temporal, PagerDuty, AutoGen, Camunda,
FIPA/BDI, scikit-learn calibration) carries all ten capabilities in one decision object.
See [comparators.md](../06-research/01-positioning/comparators.md) for the full matrix.

**Audit and liability:** Because every decision carries a `verb`, `reason_code`, `score
breakdown` and `decision_id` at the moment it is made, LAIX produces a complete audit trail
without log mining. See [eu-liability.md](../06-research/05-governance/eu-liability.md) for the
mapping to EU Product Liability Directive 2024/2853.

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

The planner contract is in place: `EnginePolicy` wraps JEV, an optimizer or a planner. The built-in
`UtilityEngine`, [MDPEngine](../02-core/06-engines.md#what-an-mdp-is) and `POMDPEngine` are
available behind the same adapter; simulation, calibration and model learning support them. See
[the planner reference](../02-core/06-engines.md).

Core vs app kit vs host is defined in [boundaries](scope-and-boundaries.md).
