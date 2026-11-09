# laix (Python)

**LAIX — Live AI Experience — is the live decision layer for AI agents that act in the real world.**

This package contains the contracts, generic policies, decision loop, execution, outcomes and decision
records. It is the Python surface of LAIX.

The package uses the Python standard library and its own modules. It takes generic inputs and
returns generic decisions.

## The two entry points

For a decision only, use the decision layer:

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

For a decision plus the loop, execution, traces and records, use the app kit:

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
| `decision/` | contract, domain, decision engines, sensing, learning, evaluation, schema and support |
| `appkit/` | `DecisionClient`, decision loop, streaming, execution, stores, platform, delivery, bench, CLI and MCP |

The full module map is in
[repository structure](../../../docs/05-project/01-repository/01-repository-structure.md); the
public names are in the [API map](../../../docs/05-project/01-repository/02-api-map.md).

## Custom policies

A policy is any object with a name and a `decide` method. Pass it to the decision layer:

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

## Operations

- `FileStateStore` and `FileOutcomeStore` add file-backed stores.
- `RetryPolicy`, `execute_async` and `run_steps_async` add retries, async handlers and timeouts.
- `decision_attributes` maps a decision onto OpenTelemetry span attributes.
- `laix explain` and `laix lint` inspect a decision JSON.
- `laix-mcp` exposes `decide` over stdio to an MCP client (`pip install "laix[mcp]"`).

## Test

```powershell
py -m pytest -q
```

## Status

Pre-1.0. The evidence is internal benchmarks and a synthetic continuity test; external validation is pending.
