# laix (Python)

One package for the LAIX decision layer: contracts, generic policies, runtime, execution, outcomes
and decision records.

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
from laix import DecisionRequest, Layer

layer = Layer()
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
- `situation` and `options` for action selection.

Both return `laix.Decision`, one shape with `verb`, `confidence`, `reason_code`, `rationale`,
`evidence`, `intent`, `requires_approval`, `score`, `breakdown`, `cost_of_waiting`, `reversible`,
`undo_hint`, `decision_id`, `trace_id`, `deliver`, `record` and `created_at`.

## Inside the package

| Piece | Role |
|---|---|
| `core/dispatch.py` | `decide()` and `select()`: the core request-to-decision entry point |
| `core/decisions/request/` | `decision_request.py` envelope and `payload/` records |
| `core/decisions/response/` | `decision.py` and `payload/` (evidence ref, intent, score breakdown) |
| `core/decisions/trail/` | execution receipt and trace |
| `core/decisions/normalise.py` | `coerce` and `from_attention` |
| `core/schema/` | `RECORDS`, `RECORD_NAMES`, schema generation, validation and `laix-v1.schema.json` |
| `core/support/` | time, ids, values, serialization, errors, verb and version helpers |
| `appkit/layer.py` | the app-kit `Layer`: core selection plus runtime, execution and traces |
| `core/engines/policies/implementations/action.py` | built-in action-selection policy |
| `core/engines/policies/implementations/active_perception.py` | packaged `observe` policy |
| `core/engines/policies/implementations/safety_constrained.py` | risk-limited action policy |
| `core/engines/policies/implementations/replanning.py` | feasible-plan selection policy |
| `core/engines/policies/implementations/allocation.py` | budgeted allocation policy |
| `core/engines/policies/implementations/negotiation.py` | accept, counter or escalate policy |
| `core/engines/policies/implementations/preference_elicitation.py` | preference-question selection policy |
| `core/engines/policies/implementations/verification.py` | outcome confirmation policy |
| `core/engines/policies/implementations/escalation.py` | hand-over policy |
| `core/engines/policies/implementations/bandit.py` | learned bandit policy |
| `core/engines/policies/policy.py`, `core/engines/policies/registry.py` | policy plugin protocol and registry |
| `core/engines/attention/input/`, `output/`, `attention.v1.json` | attention records and decision cases |
| `core/engines/attention/gates/implementations/` | one file per gate, ordered by `rules.py` |
| `core/engines/attention/decide.py`, `timing.py` | attention loop and quiet hours |
| `appkit/runtime/decision_runtime.py` | the action runtime |
| `appkit/runtime/execution.py` | approval gate, execute, cancel, undo, receipts |
| `core/sensing/` | detector, detection and frame records |
| `appkit/live_context/` | host-driven detector loop and function-backed detector |
| `appkit/runtime/state.py` | experience state: goals, phase, beliefs, decay, expiry |
| `appkit/runtime/state_store.py`, `in_memory_state_store.py` | state store contract and in-memory store |
| `core/engines/resources/` | cheap/deep call admission under budget |
| `appkit/platform/` | south platform interface, records and in-memory platform |
| `core/outcome_learning/` | directed metric ledger, store, UCB learner, and attention feedback learning |
| `appkit/audit/decision_record.py` | decision record lifecycle: draft, approve, reject, execute, undo, verify |
| `appkit/audit/proposal.py` | storage-free proposal and approval lifecycle |
| `appkit/delivery/` | delivery port, receipt and null delivery |
| `core/evaluation/` | policy parity, attention replay, and `attention-bench.v1.json` |
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
from laix import Layer

layer = Layer(policy=MyPolicy())
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
