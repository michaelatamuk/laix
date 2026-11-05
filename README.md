# LAIX

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)

LAIX is **Live AI Experience**: the decision layer for live AI experiences. A live experience is not
a chat transcript. It notices the moment, decides whether to intervene and knows when to wait. LAIX
does not generate the experience; it decides what the experience should do next.

> Given what is happening, what the app can do and what the host allows, should this experience
> **wait, observe, guide, ask, act, verify or escalate**?

| | |
|---|---|
| **Is** | the decision layer for live AI experiences |
| **Is not** | an agent framework, workflow engine, chatbot platform, database or UI kit |
| **Replaces** | scattered decision logic for when and how an AI experience should intervene |

The app owns the experience, data, UI and execution. LAIX owns the moment-to-decision loop and
records what happened.

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
`ExecutionBridge.run_steps` or `Saga` compensate completed steps when a later step fails.
`CommitmentLedger` can persist through a `CommitmentStore`.

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
[boundaries](docs/04-concepts/boundaries.md).

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
