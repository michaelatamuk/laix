# LAIX — Live AI Experience

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)

**LAIX — Live AI Experience — is the decision layer for live AI experiences.**

A live experience stays present: it notices the moment, chooses the next move and learns from what
happened. LAIX gives that loop a single decision contract. The host owns the experience; LAIX owns
the decision.

> **What should this experience do next?**

LAIX turns the moment, the options the host can offer and the limits the host sets into one decision:
**wait, observe, guide, ask, act, verify or escalate**.

The same reason, confidence, action and trail travel with every decision. The experience keeps
moving; LAIX keeps the next move decidable.

| Start | |
|---|---|
| [Quickstart](docs/01-start/quickstart.md) | install and make one decision |
| [Documentation](docs/README.md) | start, core, app kit, concepts and project |
| [Examples](examples/README.md) | runnable Python and TypeScript examples |

## One decision call

The core package answers a request directly:

```python
from laix import Context, DecisionRequest, Signal, decide

decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(
            Signal(id="s-1", kind="deadline", severity="high", confidence=0.9),
        ),
        context=Context(now="2026-11-01T10:00:00+00:00", quiet_hours=None),
    )
)[0]

print(decision.verb, decision.reason_code, decision.score)
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

Both requests return the same `Decision` shape, and every decision gets an id. TypeScript exposes the
same surface:

```ts
import { Layer } from "laix";

const [decision] = new Layer().decide({
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
  situation,
  options,
});
```

## What LAIX provides

| Capability | What it gives the host |
|---|---|
| Decision contract | one `Decision` shape for attention, action and follow-up |
| Attention | which signal deserves attention now, and what to do with it |
| Action policies | the next move from the options the app can afford |
| Packaged policies | active perception, safety, replanning, allocation, negotiation, preference, verification and escalation |
| Decision engines | utility, MDP and POMDP planners behind `EnginePolicy` |
| Learning | outcome labels, rewards, bandits, causal attribution, calibration and model learning |
| Streaming | event time, cadence, backpressure, revisions, checkpoints and sources |
| Execution | receipts, idempotency, unknown outcomes, reconciliation, sagas and records |
| Stores | state, checkpoints, commitments and outcomes through host-owned ports |
| Delivery | a port and a receipt for the app’s own channel |
| Proof | LAIX-Bench, conformance vectors, simulator, engine bench and metrics |

## Core and app kit

- **`laix.core`** — `decide(request)`, contracts, decision shape, attention, policies, engines,
  sensing contracts, resource admission, outcomes, causal attribution, calibration and evaluation.
- **`laix.appkit`** — optional integration: `Layer`, streams and checkpoints, execution and sagas,
  records, delivery, platform, live-context loop and state.

A host that needs the answer calls `decide(request)`. A host that also executes, records or delivers
calls `Layer`. See [boundaries](docs/04-concepts/boundaries.md).

## Repository map

| Path | Contents |
|---|---|
| `packages/python/laix` | the Python package: contracts, policies, engines, runtime, execution, outcomes and records |
| `packages/typescript/laix` | the TypeScript package with the same decision surface |
| `packages/contracts/` | the JSON Schema and behavioural vectors |
| `examples/` | runnable Python and TypeScript examples, grouped by lifecycle |
| `docs/` | [start, core, app kit, concepts and project](docs/README.md) |

## Test

```powershell
cd packages/python/laix
py -m pytest -q
py -m laix.appkit.bench

cd ../../packages/typescript/laix
npm test
npm run conformance
npm run bench
```

CI runs the same checks in `.github/workflows/ci.yml`. Python and TypeScript examples run there too.

## Status

Current release: `0.9.0`. Python and TypeScript share the same decision contract, policies, engines,
streaming, execution, learning and app-kit surface. LAIX-Bench passes 25/25 cases; attention
conformance passes 24/24 decisions.
