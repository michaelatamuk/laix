![LAIX — the live decision runtime with decision continuity for AI agents and automations](docs/assets/banner.png)

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![Node 22+](https://img.shields.io/badge/node-22%2B-339933?logo=node.js&logoColor=white)

# LAIX — Live AI Experience

**LAIX is the live decision runtime for AI agents and automations that act in the real world.**

Agent frameworks plan. Workflow engines orchestrate. LAIX decides whether to act, ask, wait, verify
or escalate — and makes the choice explicit, scored and auditable.

One contract for utility, commitments, execution risk and human attention — with **decision
continuity**: every decision carries its commitments, attention budget, approvals and revisions into
the next. The host owns execution, data, delivery and storage; LAIX owns the decision and its trail.

LAIX is **training-free**: the default path is deterministic policies and planners; a planner can use
a model the host supplies.

**Who it is for:** teams building AI agents or automations that take real actions — especially when
approvals, promises, human attention or auditability matter.

**Status:** `0.9.0` · synthetic evidence complete · external validation pending.

## Contents

- [Install](#install)
- [One decision](#one-decision)
- [Integrated live decision](#integrated-live-decision)
- [How it works](#how-it-works)
- [Decision continuity](#decision-continuity)
- [Results](#results)
- [Documentation](#documentation)
- [Contributing](#contributing)

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

## How it works

![How LAIX works: an agent plans, LAIX decides, the host executes, and the outcome returns as the next decision](docs/assets/how-it-works.svg)

An agent or automation plans the task. LAIX decides the next move. The host executes it. The
receipt and outcome close the loop and calibrate the next decision.

Every decision carries a verb, a reason code, confidence, a score, approval state and a trace.

## Decision continuity

A decision is one step in a sequence. It leaves state for the next decision.

| Step | Decision | State carried forward |
|---|---|---|
| 1 | acts, creating commitment `c1` | `c1` open; attention budget 0.6 spent |
| 2 | asks because `c1` is due and the budget is low | `c1` still open; approval pending |
| 3 | verifies after execution | `c1` fulfilled; receipt and outcome recorded |

The next decision sees the commitments, attention budget, approvals, revisions and outcomes the
previous one left. See [Decision continuity](docs/02-core/08-decision-continuity.md).

## What you get

| Capability | What it covers |
|---|---|
| Decision contract | one `Decision` shape for attention, action, follow-up and execution |
| Decision continuity | commitments, budget, approvals, revisions and outcomes carried into the next decision |
| Policies | action, safety, replanning, allocation, negotiation, preference, verification and escalation |
| Planners | UtilityEngine, CommitmentAwareEngine, ExecutionAwareEngine, AttentionAwareEngine, LiveDecisionEngine, MDPEngine and POMDPEngine |
| Learning | rewards, bandits, causal attribution, calibration and decision calibration |
| Streaming and execution | event time, checkpoints, timeline, receipts, recovery and records |
| App kit | stores, platform, delivery, live context and bench |

## Why LAIX

- **The core stays stateless.** Commitment, budget and execution state live in the request, so the
  host owns storage and [decision continuity](docs/02-core/08-decision-continuity.md) stays explicit
  rather than hidden in a memory layer.
- **The integration is the decision.** Utility, commitments, execution risk and attention are scored
  in one plan, not by separate policies that can silently cancel each other out.
- **The reason is part of the result.** Every decision carries its reason code, score breakdown and
  trace, so audit is produced at decision time, not reconstructed from logs. The mapping to EU
  Product Liability Directive 2024/2853 is in
  [eu-liability.md](docs/06-research/05-governance/eu-liability.md).

The proof object is `LiveDecisionEngine`: one plan that keeps a promise, avoids an irreversible action
and respects an attention budget. The contribution is the composition; see
[comparators](docs/06-research/01-positioning/comparators.md) and the
[evidence map](docs/06-research/02-evaluation/evidence-map.md).

## Results

`LiveDecisionEngine` scores **30/30** on the frozen 30-case test split and **6/6** on the conflict
cases. The hand-built glue baseline scores 28/30; the **+6.7 pp** difference is **not yet
significant** (p = 0.48). Every single-concern planner has significantly lower accuracy
(McNemar p ≤ 0.008).

![Accuracy and conflict accuracy on the frozen test split](docs/assets/benchmark.png)

| Measure | `LiveDecisionEngine` | Best comparator |
|---|---:|---:|
| Accuracy, all 30 cases | **100%** | 93.3% (glue baseline) |
| Conflict accuracy, 6 cases | **100%** | 100% (glue baseline) |
| Promise keeping | **100%** | 100% (glue baseline) |
| Irreversible actions | **0%** | 0% (glue baseline) |
| Attention-budget violations | **0%** | 0% (glue baseline) |
| p95 decision latency | **0.22 ms** | — |

The glue baseline matches `LiveDecisionEngine` on conflict, promises, reversibility and budget. The
remaining difference is accuracy on the other 24 cases, and it is not significant on 30 cases.

### Ablations

![Ablation accuracy on the frozen test split](docs/assets/ablation.png)

Removing commitments costs **30 accuracy points** (100% → 70%); removing execution risk costs
**16.7** (→ 83.3%); removing attention costs **3.3** (→ 96.7%). The equal-weights variant also scores
100%, so on this corpus the gain comes from including the concerns, not from tuning their weights.

### Verification

| Check | Result |
|---|---:|
| Python tests | 396 |
| TypeScript tests | 172 |
| Attention conformance | 24/24 |
| LAIX-Bench | 25/25 |
| Python/TypeScript parity | 210/210 |
| Invariants | 17/17 |
| Live corpus | 120 cases: 72 dev / 30 test / 18 adversarial |

The LangGraph adapter runs the same engine on 120 decisions at 6–7 ms mean with 0 interrupts.

Reproduce with `bash scripts/novelty/reproduce.sh`. Raw data:
[results/live-decision-benchmark/](results/live-decision-benchmark/README.md).

External validation — real incident replay or a participant study — is still pending.

## Documentation

| Page | Covers |
|---|---|
| [Documentation index](docs/README.md) | start, core, app kit, concepts, project and research |
| [Quickstart](docs/01-start/02-quickstart.md) | install and first decision |
| [Decision lifecycle](docs/01-start/03-decision-lifecycle.md) | moment to outcome in one loop |
| [Core building blocks](docs/02-core/00-architecture.md) | the live decision runtime |
| [Commitments](docs/02-core/07-commitments.md) | promises, ledgers, due times and dependencies |
| [App-kit building blocks](docs/03-appkit/00-architecture.md) | streaming, execution, stores and delivery |
| [Deployment](docs/03-appkit/10-deployment.md) | production topology, reliability, rollout and retention |
| [Research and evidence](docs/06-research/README.md) | claim, prior art, experiments and paper plan |
| [Privacy](docs/04-concepts/privacy.md) | what may be shared, stored or exported |
| [Security](docs/04-concepts/security.md) | threat model, trust boundaries and controls |
| [Testing](docs/05-project/testing.md) | pytest, ruff, tsc, bench, conformance and CI |
| [Troubleshooting](docs/05-project/troubleshooting.md) | symptoms, reason codes and execution failures |
| [Migration](docs/05-project/migration.md) | upgrades, compatibility and deprecation |
| [API map](docs/05-project/api-map.md) | the public surface by role |
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

For setup, design rules and the pull-request checklist, read [CONTRIBUTING.md](CONTRIBUTING.md).
Questions go to [SUPPORT.md](SUPPORT.md); participation is covered by
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately through [SECURITY.md](SECURITY.md); the
[security and threat model](docs/04-concepts/security.md) explains the boundaries.

## Citation

If you use LAIX in research, cite it via [CITATION.cff](CITATION.cff).

## License and status

Apache-2.0. See [LICENSE](LICENSE).

Current release: `0.9.0`. Python and TypeScript share the same decision contract, policies, planners,
streaming, execution, learning and app-kit surface. See [CHANGELOG.md](CHANGELOG.md).
