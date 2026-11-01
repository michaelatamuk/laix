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

Both return `laix.LayerDecision`, one shape with `verb`, `confidence`, `reason_code`, `rationale`,
`evidence`, `requires_approval`, `score`, `breakdown`, `intent`, `escalation`,
`cost_of_waiting`, `reversible`, `undo_hint`, `trace_id`, `deliver`, `record` and `created_at`.

## Inside the package

| Piece | Role |
|---|---|
| `core/contracts.py` | versioned records: observation, belief, goal, constraint, action, situation, decision, outcome, receipt, trace |
| `core/decisions.py` | the one decision shape, request shape and policy-result conversions |
| `appkit/layer.py` | the public `Layer` orchestrator |
| `core/policies/action.py` | built-in action-selection policy |
| `core/policies/active_perception.py` | packaged `observe` policy |
| `core/policies/safety.py` | risk-limited action policy |
| `core/policies/replanning.py` | feasible-plan selection policy |
| `core/policies/allocation.py` | budgeted allocation policy |
| `core/policies/negotiation.py` | accept, counter or escalate policy |
| `core/policies/preference.py` | preference-question selection policy |
| `core/policies/verification.py` | outcome confirmation policy |
| `core/policies/escalation.py` | hand-over policy |
| `core/policies/bandit.py` | learned bandit policy |
| `core/policies/registry.py` | policy plugin protocol and registry |
| `core/attention/` | attention policy: gates, score, quiet hours, budget, feedback, replay |
| `appkit/runtime/decision_runtime.py` | the action runtime |
| `appkit/runtime/execution.py` | approval gate, execute, cancel, undo, receipts |
| `core/perception.py` | detector, detection and frame contracts |
| `appkit/live_context.py` | host-driven detector loop |
| `appkit/runtime/state.py` | experience state: goals, phase, beliefs, decay, expiry |
| `appkit/runtime/state_store.py` | storage-free state store contract and in-memory store |
| `core/resources.py` | cheap/deep call admission under budget |
| `appkit/platform.py` | south platform interface and in-memory platform |
| `core/outcome.py` | directed metric ledger, outcome store contract and UCB learner |
| `appkit/records/decision.py` | decision record lifecycle: draft, approve, reject, execute, undo, verify |
| `appkit/records/proposal.py` | storage-free proposal and approval lifecycle |
| `appkit/delivery.py` | delivery port and receipt |
| `core/evaluation.py` | policy parity and replay harness |
| `appkit/bench.py` | LAIX-Bench suites, report and `python -m laix.appkit.bench` |
| `core/schema.py` | generated JSON Schema |

## Custom policies

A policy is any object with a name and a `decide` method:

```python
from laix import DecisionRequest, Layer, LayerDecision

class MyPolicy:
    name = "my-policy"
    version = "1.0"

    def decide(self, request):
        return [LayerDecision(verb="wait", confidence=0.5, reason_code="policy_rule", rationale="wait")]

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
