# LAIX

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)

LAIX is one decision layer for live apps. An app describes the moment and its limits. LAIX decides
whether to **wait, observe, guide, ask, act, verify or escalate**, and records what happened.

## One decision call

The core package answers a request without importing the app kit:

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

An app can ask LAIX to choose between actions in the same way:

```python
decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=options,
    )
)[0]
```

Both requests return the same `Decision` shape, and every decision gets an id.

When the app also needs execution, traces, records or delivery, use `Layer` from the app kit:

```python
from laix import DecisionRequest, Layer

layer = Layer()
decisions = layer.decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=options,
    )
)
```

`Layer` uses the same core selection and adds the runtime, execution and audit parts.

## Inside the layer

The layer holds one set of contracts and two built-in policies:

- **attention**: which signal deserves attention now, and what should the app do with it?
- **action decision**: which option should the app choose?

It also ships eight packaged policies for active perception, safety-constrained action, replanning,
allocation, negotiation, preference elicitation, verification and escalation. They use the same
plugin interface and decision shape. `EnginePolicy` wraps an external engine — JEV, an optimizer or a
planner — behind that same interface, and `RulePolicy` / `TargetedPolicy` cover authored rules and
group targets.

Built-in engines add `UtilityEngine`, `MDPEngine` and `POMDPEngine`. `Simulator` compares engines on
the same scenario, `CalibrationReport` compares confidence with accuracy, and `ModelLearner` learns
transitions and rewards with rollback.

Live Context adds a detector contract and a perception loop: cheap detectors run continuously, deep
ones are admitted under a sub-second cost and latency budget, and each event produces a frame.

`Layer.stream` adds the live loop around decisions: event time, cadence, backpressure and revisions.
`StreamSession` saves and resumes through a `StreamCheckpointStore` and reads NDJSON or SSE sources.
The execution bridge adds idempotency keys, unknown outcomes and reconciliation around a write, and
`Saga` compensates completed steps when a later step fails.

Outcome learning turns measured labels into rewards. `UCBBandit` learns which arm works and
`BanditPolicy` puts that learner behind the policy interface. `CausalLedger` estimates a treatment
effect, `CommitmentLedger` and `PlanningPolicy` plan the next step, `GroupPolicy` masks private
state, and `ShadowPolicy` compares a second policy without changing the primary decision.

LAIX-Bench runs deterministic cases for every decision class:

```powershell
python -m laix.appkit.bench
```

New apps send requests. Shared rules become generic policies. App rules stay in the app adapter.

## Two surfaces

- **`laix.core`** — `decide(request)`, contracts, decision shape, attention, policies, decision engines, sensing contracts, resource admission, outcomes, causal attribution, calibration and evaluation. Core uses only core modules.
- **`laix.appkit`** — optional integration: Layer, streams and checkpoints, execution and sagas, records, delivery, platform, live-context loop and state.

A host that only needs the answer calls `decide(request)`. A host that also executes, records or
delivers calls `Layer`. LAIX uses its own modules and generic vocabulary. See
[boundaries](docs/boundaries.md).

## Repository map

| Path | Contents |
|---|---|
| `packages/python/laix` | one Python package: contracts, policies, engines, runtime, execution, outcomes, records |
| `packages/typescript/laix` | one TypeScript package: the decision contract, policies, engines and app kit |
| `packages/contracts/` | the JSON Schema and behavioural vectors |
| `examples/` | small runnable requests in Python and TypeScript |
| `docs/` | [design notes, guides and the integration guide](docs/README.md) |

## Test

```powershell
cd packages/python/laix
py -m pytest -q
py -m laix.appkit.bench

cd ../../packages/typescript/laix
npm test
npm run conformance
```

CI runs the same checks in `.github/workflows/ci.yml`.

## Status

Early seed. The contracts, policies and engines pass their vectors. The 2027 figures in the LAIX
notes are goals.
