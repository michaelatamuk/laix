# LAIX

LAIX is one decision layer for live apps. An app describes the moment and its limits. LAIX decides
whether to **wait, observe, guide, ask, act, verify or escalate**, and records what happened.

## One package, one API

There is one Python package and one TypeScript package. The main object is `Layer`:

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

An app can ask LAIX to choose between actions in the same way:

```python
decisions = layer.decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=options,
    )
)
```

Both requests return the same `Decision` shape. The app sends one request, and LAIX uses a generic
policy.

## Inside the layer

The layer holds one set of contracts and two generic policies:

- **attention**: which signal deserves attention now, and how?
- **action**: which of the available actions should the app take?

New apps send requests. Shared rules become generic policies. App rules stay in the app adapter.

## Repository map

| Path | Contents |
|---|---|
| `python/laix` | one Python package: contracts, policies, runtime, execution, outcomes, records |
| `typescript/laix` | one TypeScript package: the decision contract, attention policy and decision record |
| `contracts/` | the JSON Schema and behavioural vectors |
| `eval/` | the benchmark seed |
| `examples/` | small runnable requests in Python and TypeScript |
| `docs/` | design notes |

## Test

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-all.ps1
```

The script runs the Python package, the TypeScript package and the contract conformance check.

## Status

Early seed. The contracts and policies pass their vectors. The 2027 figures in the LAIX notes are
goals.
