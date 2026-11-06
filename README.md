# LAIX — Live AI Experience

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**LAIX is the decision runtime for AI agents and automations that act in the real world.**

Agent frameworks plan. Workflow engines orchestrate. LAIX decides whether to act, ask, wait, verify
or escalate — and records why.

One contract for utility, commitments, execution risk and human attention. The host owns execution,
data, delivery and storage; LAIX owns the decision and its trail.

LAIX is **training-free**: the default path is deterministic policies and planners; a planner can use
a model the host supplies.

**Status:** `0.9.0` · synthetic evidence complete · external validation pending.

## Contents

- [Install](#install)
- [One decision](#one-decision)
- [Integrated live decision](#integrated-live-decision)
- [What you get](#what-you-get)
- [Why LAIX](#why-laix)
- [Proof](#proof)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License and status](#license-and-status)

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.9.0#subdirectory=packages/python/laix"
```

From a local checkout, at the repository root:

```powershell
pip install -e packages/python/laix
```

TypeScript, from a local checkout (the package is not published to npm yet):

```powershell
npm install file:../path/to/laix/packages/typescript/laix
```

The Python package needs Python 3.11 or newer. The TypeScript package needs Node 22 or newer.
See the [quickstart](docs/01-start/02-quickstart.md) for the full setup.

## One decision

```python
from datetime import datetime, timezone

from laix import Context, DecisionRequest, Signal, decide

decision = decide(
    DecisionRequest(
        subject="one decision",
        at="2026-11-01T10:00:00+00:00",
        signals=(
            Signal(id="s-1", kind="deadline", severity="high", confidence=0.9),
        ),
        context=Context(
            now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
            quiet_hours=None,
        ),
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

Every decision carries a verb, a reason code, confidence, an action and the identifiers that
connect it to the audit trail.

## Integrated live decision

`LiveDecisionEngine` scores the options on utility, promises, execution risk and human attention,
then returns one plan with the full breakdown.

```python
from laix import ActionOption, Commitment, DecisionProblem, LiveDecisionEngine

plan = LiveDecisionEngine().solve(
    DecisionProblem(
        subject="send the report",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="now",
                verb="act",
                name="send now",
                expected_benefit=1.0,
                reversible=False,
                params={"commitments": {"violates": ["c1"]}},
            ),
            ActionOption(
                id="ask",
                verb="ask",
                name="ask first",
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

print(plan.action_id, plan.reason_code)
```

The plan prefers the reversible, promise-keeping option and keeps the commitment, execution and
attention scores. See the full
[conflict scenario](examples/python/03-plan/conflict_scenario.py).

## What you get

| Capability | What it gives the host |
|---|---|
| Decision contract | one `Decision` shape for attention, action, follow-up and execution |
| Policies | action, safety, replanning, allocation, negotiation, preference, verification and escalation |
| Planners | utility, commitment, execution, attention, integrated live, MDP and POMDP |
| Learning | rewards, bandits, causal attribution, calibration and decision calibration |
| Streaming and execution | event time, checkpoints, timeline, receipts, recovery and records |
| App kit | stores, platform, delivery, live context and bench |

## Why LAIX

- **One decision contract** — attention, action, follow-up, execution and outcomes share the same
  shape, reasons, confidence and trail.
- **Training-free** — no training or fine-tuning; deterministic policies and planners, with an
  optional model the host supplies.
- **Live context is part of the decision** — promises, execution risk and human attention are scored
  in the same plan.
- **The host keeps control** — LAIX decides; the host owns data, execution, storage and delivery.
- **Inspectable** — reason code, score breakdown, decision id, trace, conformance vectors and
  Python/TypeScript parity.

The contribution is the integration, not a new algorithm. See
[comparators](docs/06-research/01-positioning/comparators.md) and the
[evidence map](docs/06-research/02-evaluation/evidence-map.md).

Because every decision carries its reason and score at the moment it is made, LAIX produces an audit
trail without log mining. The mapping to EU Product Liability Directive 2024/2853 is in
[eu-liability.md](docs/06-research/05-governance/eu-liability.md).

## Proof

| Check | Result |
|---|---|
| Python tests | pass |
| TypeScript tests | 172 |
| Attention conformance | 24/24 |
| LAIX-Bench | 25/25 |
| Live corpus | 120 cases: 72 dev / 30 test / 18 adversarial |
| Live test split | `live` 30/30; glue 28/30; conflict 6/6 |
| Python/TypeScript parity | 210/210 |
| Invariants | 17/17 |

The 120-case live corpus and the 7-case ablation demo are separate. On the frozen 30-case test split,
`live` is 30/30 and a hand-built glue baseline is 28/30; the difference is not yet significant. The
7-case demo shows the single-concern planners fail when concerns conflict. See
[Testing](docs/05-project/testing.md) for the commands.

External validation — real incident replay or a participant study — is still pending.

## Documentation

| Page | Covers |
|---|---|
| [Documentation index](docs/README.md) | start, core, app kit, concepts, project and research |
| [Quickstart](docs/01-start/02-quickstart.md) | install and first decision |
| [Decision lifecycle](docs/01-start/03-decision-lifecycle.md) | moment to outcome in one loop |
| [Core building blocks](docs/02-core/00-architecture.md) | the decision runtime |
| [App-kit building blocks](docs/03-appkit/00-architecture.md) | streaming, execution, stores and delivery |
| [Research and evidence](docs/06-research/README.md) | claim, prior art, experiments and paper plan |
| [Privacy](docs/04-concepts/privacy.md) | what may be shared, stored or exported |
| [Testing](docs/05-project/testing.md) | pytest, ruff, tsc, bench, conformance and CI |
| [Repository structure](docs/05-project/repository-structure.md) | where each package, module and test lives |
| [Examples](examples/README.md) | Python and TypeScript, grouped by lifecycle |

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

CI runs the same checks on every push, plus the live benchmark, TypeScript parity, examples and docs
links. See [Testing](docs/05-project/testing.md) for every check.

## License and status

Apache-2.0. See [LICENSE](LICENSE).

Current release: `0.9.0`. Python and TypeScript share the same decision contract, policies, planners,
streaming, execution, learning and app-kit surface. See [CHANGELOG.md](CHANGELOG.md).
