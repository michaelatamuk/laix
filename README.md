# LAIX

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)

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

The layer holds one set of contracts and two common request policies:

- **attention**: which signal deserves attention now, and how?
- **action**: which of the available actions should the app take?

It also ships reference policy packs for active perception, safety-constrained action, replanning,
allocation, negotiation, preference elicitation, verification and escalation. They use the same
plugin interface and decision shape.

Live Context adds a detector contract and a perception loop: cheap detectors run continuously, deep
ones are admitted under a sub-second cost and latency budget, and each event produces a frame.

Outcome learning turns measured labels into rewards. `UCBBandit` learns which arm works and
`BanditPolicy` puts that learner behind the policy interface.

LAIX-Bench runs deterministic cases for every decision class:

```powershell
python -m laix.bench
```

New apps send requests. Shared rules become generic policies. App rules stay in the app adapter.

## Repository map

| Path | Contents |
|---|---|
| `packages/python/laix` | one Python package: contracts, policies, runtime, execution, outcomes, records |
| `packages/typescript/laix` | one TypeScript package: the decision contract, attention policy and decision record |
| `packages/contracts/` | the JSON Schema and behavioural vectors |
| `examples/` | small runnable requests in Python and TypeScript |
| `docs/` | [design notes, guides and the integration guide](docs/README.md) |

## Test

```powershell
cd packages/python/laix
py -m pytest -q
py -m laix.bench

cd ../../packages/typescript/laix
npm test
npm run conformance
```

CI runs the same checks in `.github/workflows/ci.yml`.

## Status

Early seed. The contracts and policies pass their vectors. The 2027 figures in the LAIX notes are
goals.
