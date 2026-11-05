# LAIX — Live AI Experience

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)

**LAIX — Live AI Experience — is the decision layer for live AI experiences.**

A live experience is always in the loop: it notices what is changing, decides what matters and acts
before the moment passes. LAIX gives that loop a single decision contract. The host owns the
experience; LAIX owns the decision.

> **What matters now, and what should the experience do about it?**

LAIX turns what is happening, the options the host can offer and the limits the host sets into one
decision: **wait, observe, guide, ask, act, verify or escalate**.

The same reason, confidence, action and trail travel with every decision. The experience stays
present; LAIX keeps the next move timely.

LAIX is **training-free**. The current layer uses policies, rules and planners over a model the host
supplies.

| Start | |
|---|---|
| [Quickstart](docs/01-start/quickstart.md) | install and make one decision |
| [Lifecycle](docs/01-start/decision-lifecycle.md) | moment to outcome in one loop |
| [Documentation](docs/README.md) | start, core, app kit, concepts and project |
| [FAQ](docs/04-concepts/faq.md) | models, execution and novelty |
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

The snippets assume the app has already built `situation` and `options`.

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

For the integrated live decision, the same `DecisionProblem` goes to `LiveDecisionEngine`:

```python
from laix import LiveDecisionEngine

plan = LiveDecisionEngine().solve(problem)
```

## Why LAIX

- **One decision contract** — attention, action, follow-up, execution and outcomes share the same
  shape, reasons, confidence and trail.
- **Training-free** — policies and rules now; planners use a model the host supplies.
- **Live context is part of the decision** — promises, execution risk and human attention are scored
  in the plan; calibration and decision time complete the loop.
- **The host keeps control** — LAIX decides; the host owns data, execution, storage and delivery.
- **Inspectable and testable** — reasons, trail, conformance vectors, bench and Python/TypeScript
  parity.

The novelty is the combination: a model-free decision layer that treats commitments, execution
risk, human attention, calibration and decision time as one contract.

`LiveDecisionEngine` makes that concrete: one plan can keep a promise, avoid an irreversible action
and respect an attention budget at the same time. Calibration and the decision timeline complete the
loop around that plan.

## What LAIX provides

| Capability | What it gives the host |
|---|---|
| Decision contract | one `Decision` shape for attention, action and follow-up |
| Attention | which signal deserves attention now, and what to do with it |
| Action policies | the next move from the options the app can afford |
| Packaged policies | active perception, safety, replanning, allocation, negotiation, preference, verification and escalation |
| Planners | [utility, commitment, execution, attention, integrated live, MDP and POMDP](docs/02-core/06-engines.md) behind `EnginePolicy` |
| Learning | outcome labels, rewards, bandits, causal attribution, calibration, decision calibration and model learning |
| Streaming | event time, cadence, backpressure, revisions, checkpoints, timeline and sources |
| Execution | receipts, idempotency, unknown outcomes, reconciliation, multi-step recovery and records |
| Stores | state, checkpoints, commitments and outcomes through host-owned ports |
| Delivery | a port and a receipt for the app’s own channel |

## Proof

| Check | Result |
|---|---|
| Python tests | passed |
| TypeScript tests | 172 passed |
| Attention conformance | 24/24 |
| LAIX-Bench | 25/25 |
| Live decision bench | `LiveDecisionEngine` matches 7/7 expected actions |

The single-concern planners win their own cases: utility on plain benefit, commitment on promises,
execution on irreversible or unknown actions, attention on human-facing choices. The integrated
planner combines them.

## Core and app kit

- **`laix.core`** — `decide(request)`, contracts, decision shape, attention, policies, planners,
  sensing contracts, resource admission, outcomes, causal attribution, calibration and evaluation.
- **`laix.appkit`** — optional integration: `Layer`, streams, checkpoints and timeline, execution
  and multi-step recovery, records, delivery, platform, live-context loop and state.

A host that needs the answer calls `decide(request)`. A host that also executes, records or delivers
calls `Layer`. See [boundaries](docs/04-concepts/boundaries.md).

## Repository map

| Path | Contents |
|---|---|
| `packages/python/laix` | the Python package: contracts, policies, planners, runtime, execution, outcomes and records |
| `packages/typescript/laix` | the TypeScript package with the same decision surface |
| `packages/contracts/` | the JSON Schema and behavioural vectors |
| `examples/` | runnable Python and TypeScript examples, grouped by lifecycle |
| `docs/` | [start, core, app kit, concepts and project](docs/README.md) |
| `scripts/` | repository checks, including docs links |

## Test

```powershell
cd packages/python/laix
py -m pytest -q
py -m laix.appkit.bench
py -m laix.appkit.bench --live

cd ../../packages/typescript/laix
npm test
npm run conformance
npm run bench
```

CI runs the same checks in `.github/workflows/ci.yml`. Python and TypeScript examples run there too.

## Status

Current release: `0.9.0`. Python and TypeScript share the same decision contract, policies,
planners, streaming, execution, learning and app-kit surface. See [Proof](#proof) for the current
checks.
