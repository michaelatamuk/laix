# laix (Python)

One package for the LAIX decision layer: contracts, generic policies, runtime, execution, outcomes
and decision records.

The package uses the Python standard library and its own modules. It takes generic inputs and
returns generic decisions.

## The one API

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
`evidence`, `intent`, `requires_approval`, `score`, `breakdown`, `intent`, `escalation`,
`cost_of_waiting`, `reversible`, `undo_hint`, `trace_id`, `deliver`, `record` and `created_at`.

## Inside the package

| Piece | Role |
|---|---|
| `core/decisions/request/` | `request.py` envelope and `payload/` records |
| `core/decisions/answer/` | `decision.py` and `payload/` (evidence ref, intent, score breakdown) |
| `core/decisions/lifecycle/` | execution receipt and trace |
| `core/decisions/normalise.py` | `coerce` and `from_attention` |
| `core/schema/` | `RECORDS`, `RECORD_NAMES`, schema generation, validation and `laix-v1.schema.json` |
| `core/support/` | time, ids, values, serialization, errors, verb and version helpers |
| `appkit/layer.py` | the public `Layer` orchestrator |
| `core/policies/builtin/action/` | built-in action-selection policy |
| `core/policies/packs/active_perception.py` | packaged `observe` policy |
| `core/policies/packs/safety.py` | risk-limited action policy |
| `core/policies/packs/replanning.py` | feasible-plan selection policy |
| `core/policies/packs/allocation.py` | budgeted allocation policy |
| `core/policies/packs/negotiation.py` | accept, counter or escalate policy |
| `core/policies/packs/preference.py` | preference-question selection policy |
| `core/policies/packs/verification.py` | outcome confirmation policy |
| `core/policies/packs/escalation.py` | hand-over policy |
| `core/policies/packs/bandit.py` | learned bandit policy |
| `core/policies/policy.py`, `core/policies/registry.py` | policy plugin protocol and registry |
| `core/attention/model/`, `core/attention/ports/`, `core/attention/vectors/` | attention records, ports and test vectors |
| `core/attention/decide.py`, `timing.py`, `replay.py`, `labels.py`, `outcome_log.py` | attention policy, gates, quiet hours, replay and labels |
| `appkit/runtime/decision_runtime.py` | the action runtime |
| `appkit/runtime/execution.py` | approval gate, execute, cancel, undo, receipts |
| `core/perception/` | detector, detection and frame records |
| `appkit/live_context/` | host-driven detector loop and function-backed detector |
| `appkit/runtime/state.py` | experience state: goals, phase, beliefs, decay, expiry |
| `appkit/runtime/state_store.py`, `in_memory_state_store.py` | state store contract and in-memory store |
| `core/resources/` | cheap/deep call admission under budget |
| `appkit/platform/` | south platform interface, records and in-memory platform |
| `core/outcome/` | directed metric ledger, outcome store protocol and UCB learner |
| `appkit/audit/decision_record.py` | decision record lifecycle: draft, approve, reject, execute, undo, verify |
| `appkit/audit/proposal.py` | storage-free proposal and approval lifecycle |
| `appkit/delivery/` | delivery port, receipt and null delivery |
| `core/evaluation/` | policy parity and replay harness |
| `appkit/bench/` | LAIX-Bench cases, suites, report and `python -m laix.appkit.bench` |

## Custom policies

A policy is any object with a name and a `decide` method:

```python
from laix import DecisionRequest, Layer, Decision

class MyPolicy:
    name = "my-policy"
    version = "1.0"

    def decide(self, request):
        return [Decision(verb="wait", confidence=0.5, reason_code="policy_rule", rationale="wait")]

layer = Layer(policy=MyPolicy())
decision = layer.decide(
    DecisionRequest(subject="one decision", at="2026-11-01T10:00:00+00:00")
)[0]
```

Register and select policies at runtime:

```python
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
