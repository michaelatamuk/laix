# laix (Python)

**LAIX — Live AI Experience — is the live decision runtime for AI agents and automations that act in the real world.**

This package contains the contracts, generic policies, runtime, execution, outcomes and decision
records. It is the Python surface of LAIX.

The package uses the Python standard library and its own modules. It takes generic inputs and
returns generic decisions.

## The two entry points

For a decision only, use the core:

```python
from laix import DecisionRequest, decide

decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(signal,),
        context=context,
    )
)[0]
```

For a decision plus runtime, execution, traces and records, use the app kit:

```python
from laix import DecisionRequest, DecisionClient

layer = DecisionClient()
decisions = layer.decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(signal,),
        context=context,
    )
)
```

`DecisionRequest` carries either:

- `signals` and `context` for attention allocation; or
- `situation` and `options` for action decisions.

Both return `laix.Decision`, one shape with `verb`, `confidence`, `reason_code`, `rationale`,
`evidence`, `intent`, `requires_approval`, `score`, `breakdown`, `cost_of_waiting`, `reversible`,
`undo_hint`, `decision_id`, `trace_id`, `deliver`, `record` and `created_at`.

## Inside the package

| Piece | Role |
|---|---|
| `core/dispatch.py` | `decide()` and `select()`: the core request-to-decision entry point |
| `core/domain/decisions/request/` | `decision_request.py` envelope and `payload/` records |
| `core/domain/decisions/response/` | `decision.py` and `payload/` (evidence ref, intent, score breakdown) |
| `core/domain/decisions/trail/` | execution receipt and trace |
| `core/domain/decisions/normalise.py` | `coerce` and `from_signal_attention` |
| `core/schema/` | `RECORDS`, `RECORD_NAMES`, schema generation, validation and `laix-v1.schema.json` |
| `core/support/` | time, ids, values, serialization, errors, verb and version helpers |
| `appkit/decision_client.py` | the app-kit `DecisionClient`: core selection plus runtime, execution and traces |
| `core/contract/planner.py`, `planner_input.py`, `planner_result.py`, `planner_policy.py` | `Planner`, `PlannerInput`, `PlannerResult` and `PlannerPolicy` |
| `core/engines/decision/single/planners/` | `UtilityPlanner`, `CommitmentPlanner`, `ExecutionRiskPlanner`, `HumanAttentionPlanner`, `CAVODPlanner`, `MDPPlanner` and `POMDPPlanner` |
| `core/engines/decision/single/planners/composite/` | `LiveCompositePlanner` and `CompositeScore` |
| `core/engines/decision/sequence/` | `CABBPlanner`, `RolloutPlanner` and `ReplanPlanner` for finite-horizon sequences |
| `core/engines/decision/fleet/` | `AttentionScheduler` for fleet-level attention allocation and `WhittleScheduler` for the exact single-arm index |
| `core/engines/decision/history/` | `repair_continuity` for conflicting decision histories |
| `core/engines/decision/explain/` | `counterfactual_attribution` and `counterfactual_search` for decision explanations |
| `core/engines/decision/single/policies/implementations/action.py` | built-in action-selection policy |
| `core/engines/decision/single/policies/implementations/active_perception.py` | packaged `observe` policy |
| `core/engines/decision/single/policies/implementations/safety_constrained.py` | risk-limited action policy |
| `core/engines/decision/single/policies/implementations/replanning.py` | feasible-plan selection policy |
| `core/engines/decision/single/policies/implementations/allocation.py` | budgeted allocation policy |
| `core/engines/decision/single/policies/implementations/negotiation.py` | accept, counter or escalate policy |
| `core/engines/decision/single/policies/implementations/preference_elicitation.py` | preference-question selection policy |
| `core/engines/decision/single/policies/implementations/verification.py` | outcome confirmation policy |
| `core/engines/decision/single/policies/implementations/escalation.py` | hand-over policy |
| `core/engines/decision/single/policies/implementations/bandit.py` | learned bandit policy |
| `core/engines/decision/single/policies/implementations/rules.py` | declarative `Rule` / `RulePolicy` |
| `core/engines/decision/single/policies/implementations/target.py` | `TargetedPolicy` for recipient modes |
| `core/engines/decision/single/policies/decision_policy.py`, `core/engines/decision/single/policies/decision_policy_registry.py` | policy plugin protocol and registry |
| `core/engines/sensing/signals/input/`, `output/`, `signal-attention.v1.json` | signal-attention records and decision cases |
| `core/engines/sensing/signals/gates/implementations/` | one file per gate, ordered by `rules.py` |
| `core/engines/sensing/signals/decide.py`, `timing.py` | signal-attention loop and quiet hours |
| `appkit/runtime/decision_runtime.py` | the action-decision runtime |
| `appkit/runtime/execution.py` | approval, idempotency, execute, cancel, undo, unknown outcome, receipts |
| `core/domain/perception/` | detector, detection and frame records |
| `appkit/live_context/` | host-driven detector loop and function-backed detector |
| `appkit/streaming/` | stream session: event time, cadence, backpressure, revisions, windows |
| `appkit/runtime/state.py` | experience state: goals, phase, beliefs, decay, expiry |
| `appkit/runtime/state_store.py`, `in_memory_state_store.py` | state store contract and in-memory store |
| `core/engines/sensing/resources/` | cheap/deep call admission under budget |
| `appkit/platform/` | south platform interface, records and in-memory platform |
| `core/domain/outcomes/` | directed metric ledger, outcome store and signal-attention feedback records |
| `core/engines/learning/` | calibration, model learning, the UCB learner and causal attribution |
| `appkit/audit/decision_record.py` | decision record lifecycle: draft, approve, reject, execute, undo, verify |
| `appkit/audit/proposal.py` | storage-free proposal and approval lifecycle |
| `appkit/delivery/` | delivery port, receipt and null delivery |
| `core/engines/evaluation/cases/` | policy parity, signal attention replay, and `signal-attention-bench.v1.json` |
| `appkit/bench/` | LAIX-Bench cases, suites, report and `python -m laix.appkit.bench` |

## Custom policies

A policy is any object with a name and a `decide` method. Pass it to the core:

```python
from laix import DecisionRequest, Decision, decide

class MyPolicy:
    name = "my-policy"
    version = "1.0"

    def decide(self, request):
        return [Decision(verb="wait", confidence=0.5, reason_code="policy_rule", rationale="wait")]

decision = decide(
    DecisionRequest(subject="one decision", at="2026-11-01T10:00:00+00:00"),
    policy=MyPolicy(),
)[0]
```

The app kit keeps a policy registry:

```python
from laix import DecisionClient

layer = DecisionClient(policy=MyPolicy())
decision = layer.decide(
    DecisionRequest(subject="one decision", at="2026-11-01T10:00:00+00:00")
)[0]

layer.register_policy("my-policy", MyPolicy())
layer.use_policy("my-policy")
print(layer.status())
print(layer.explain(decision))
```

## Test

```powershell
py -m pytest -q
```

## Status

The package contains rules. The 2027 figures are goals.
