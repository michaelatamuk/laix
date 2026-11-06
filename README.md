# LAIX — Live AI Experience

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

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

## Contents

- [Install](#install)
- [One decision](#one-decision)
- [Integrated live decision](#integrated-live-decision)
- [Why LAIX](#why-laix)
- [What you get](#what-you-get)
- [Checks](#checks)
- [Documentation](#documentation)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Changelog](#changelog)
- [Status](#status)

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.9.0#subdirectory=packages/python/laix"
```

From a local checkout, at the repository root:

```powershell
pip install -e packages/python/laix
```

TypeScript, from a local checkout:

```powershell
npm install file:../path/to/laix/packages/typescript/laix
```

See the [quickstart](docs/01-start/quickstart.md) for the full setup.

## One decision

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

print(decision.verb, decision.reason_code, decision.confidence)
```

TypeScript:

```ts
import { Layer } from "laix";

const [decision] = new Layer().decide({
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "deadline", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: ["22:00", "06:00"] },
});
```

## Integrated live decision

`LiveDecisionEngine` scores the options on utility, promises, execution risk and human attention,
then returns one plan with the full breakdown.

```python
from laix import ActionOption, Commitment, DecisionProblem, LiveDecisionEngine

plan = LiveDecisionEngine().solve(
    DecisionProblem(
        subject="one live decision",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="fast",
                verb="act",
                name="fast",
                expected_benefit=1.0,
                reversible=False,
                params={"commitments": {"violates": ["c1"]}},
            ),
            ActionOption(
                id="safe",
                verb="act",
                name="safe",
                expected_benefit=0.6,
                params={"commitments": {"fulfills": ["c1"]}},
            ),
        ),
        attributes={
            "commitments": (
                Commitment(
                    id="c1",
                    subject="send the report",
                    due="2026-11-01T09:00:00+00:00",
                ),
            )
        },
    )
)

print(plan.action_id, plan.reason_code)  # safe live_decision
```

The plan keeps the promise, avoids the irreversible action and carries the commitment, execution
and attention scores.

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
risk, human attention, calibration and decision time as one contract. No compared system (LangGraph,
Temporal, PagerDuty, AutoGen, Camunda, FIPA/BDI) carries all ten capabilities in one decision
object — see [comparators.md](docs/06-research/01-positioning/comparators.md).

`LiveDecisionEngine` makes that concrete: one plan can keep a promise, avoid an irreversible action
and respect an attention budget at the same time. On the live bench, `live` wins every case (7/7);
single-concern planners win their own cases but fail when two or more concerns fire simultaneously
(`execution` 5/7, `attention` 4/7, `commitment` 3/7, `utility` 2/7). Run the ablation with one
command: `python examples/python/03-plan/ablation_study.py`.

Because every decision carries a `verb`, `reason_code`, `score breakdown` and `decision_id` at the
moment it is made, LAIX produces a complete audit trail without log mining. This directly answers
the EU Product Liability Directive 2024/2853 (applicable December 2026), which makes AI deployers
liable without proof of fault and shifts the burden to documentation. See
[eu-liability.md](docs/06-research/05-governance/eu-liability.md).

## What you get

| Capability | What it gives the host |
|---|---|
| Decision contract | one `Decision` shape for attention, action, follow-up and execution |
| Policies | action, safety, replanning, allocation, negotiation, preference, verification and escalation |
| Planners | utility, commitment, execution, attention, integrated live, MDP and POMDP |
| Learning | rewards, bandits, causal attribution, calibration and decision calibration |
| Streaming and execution | event time, checkpoints, timeline, receipts, recovery and records |
| App kit | stores, platform, delivery, live context and bench |

## Checks

CI runs the full Python and TypeScript suites, examples, bench, conformance and docs links.

Current: **conformance 24/24 · LAIX-Bench 25/25 · live corpus 120 cases (test 30/30, glue 28/30, conflict 6/6) · TS live parity 210/210 · invariants 17/17 · 172 TypeScript tests**.

See [Testing](docs/05-project/testing.md) for the full check list and how to run it.

## Documentation

| Start | |
|---|---|
| [Documentation index](docs/README.md) | start, core, app kit, concepts, project and research |
| [Decision lifecycle](docs/01-start/decision-lifecycle.md) | moment to outcome in one loop |
| [Core building blocks](docs/02-core/00-architecture.md) | the decision layer |
| [App-kit building blocks](docs/03-appkit/00-architecture.md) | streaming, execution, stores and delivery |
| [FAQ](docs/04-concepts/faq.md) | models, execution and novelty |
| [Research and evidence](docs/06-research/README.md) | claim, prior art, experiments and paper plan |
| [Privacy](docs/04-concepts/privacy.md) | what may be shared, stored or exported |
| [Examples](examples/README.md) | Python and TypeScript, grouped by lifecycle |
| [Roadmap](docs/05-project/roadmap.md) | what is done and what is next |

## Requirements

- Python 3.11 or newer (CI runs 3.11 and 3.13).
- Node 22 or newer (CI runs 22 and 24).
- TypeScript 5.9 for declaration checks.

The Python core uses the standard library. The TypeScript package has no runtime dependencies.

## Contributing

Run the full checks before opening a change:

```powershell
cd packages/python/laix
py -m pytest -q
py -m ruff check .

cd ../../packages/typescript/laix
npm test
npm run typecheck
npm run conformance
npm run bench
```

See [Testing](docs/05-project/testing.md) for every check and [Structure](docs/05-project/structure.md)
for where things live. CI runs the same checks on every push.

## License

Apache-2.0. See [LICENSE](LICENSE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Status

Current release: `0.9.0`. Python and TypeScript share the same decision contract, policies,
planners, streaming, execution, learning and app-kit surface.
