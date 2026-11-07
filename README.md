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
continuity**: every decision carries its commitments, human-attention budget, approvals and
revisions into the next. The host owns execution, data, delivery and storage; LAIX owns the
decision and its trail.

LAIX is **training-free**: the default path is deterministic policies and planners; a planner can use
a model the host supplies.

**Who it is for:** teams building AI agents or automations that take real actions — especially when
approvals, promises, human attention or auditability matter.

**Status:** pre-1.0 (`0.10.0`). Evidence: internal benchmarks and a synthetic continuity test;
external validation is pending.

[Quickstart](docs/01-start/02-first-steps/01-quickstart.md) ·
[Documentation](docs/README.md) ·
[Examples](examples/README.md) ·
[Issues](https://github.com/michaelatamuk/laix/issues)

## One decision

A payment that needs owner approval is still a confident decision. The default action policy can
choose to pay; the decision also says that a person must approve it and that the action is not
reversible.

```python
import json

from laix import (
    ActionOption,
    Belief,
    Commitment,
    DecisionRequest,
    HumanAttentionBudget,
    Situation,
    decide,
)

request = DecisionRequest(
    subject="invoice 4832",
    at="2026-11-01T10:00:00+00:00",
    situation=Situation(
        id="s-1",
        at="2026-11-01T10:00:00+00:00",
        subject="invoice 4832",
        beliefs=(
            Belief(
                id="b-1",
                proposition="the invoice matches the work order",
                confidence=0.95,
            ),
        ),
        attributes={"urgency": 0.8},
    ),
    options=(
        ActionOption(
            id="pay",
            verb="act",
            name="pay the invoice",
            expected_benefit=0.95,
            risk=0.05,
            requires_approval=True,
            reversible=False,
            interrupt_cost=0.6,
            params={"commitments": {"violates": ["c1"]}},  # pays without asking
        ),
        ActionOption(
            id="ask",
            verb="ask",
            name="ask the owner for approval",
            expected_benefit=0.6,
            interrupt_cost=0.2,
            params={"commitments": {"fulfills": ["c1"]}},  # asks before paying
        ),
        ActionOption(
            id="wait",
            verb="wait",
            name="wait for the next review",
            expected_benefit=0.2,
            interrupt_cost=0.0,
        ),
    ),
    attributes={
        "commitments": (
            Commitment(
                id="c1",
                subject="ask the owner before paying",
                due="2026-11-01T09:00:00+00:00",
            ),
        ),
        "human_attention_budget": HumanAttentionBudget(total=2.0, spent=0.5),
    },
)

decision = decide(request)[0]

print(json.dumps({
    "verb": decision.verb.value,
    "reason_code": decision.reason_code,
    "action_id": decision.action_id,
    "confidence": decision.confidence,
    "score": decision.score,
    "requires_approval": decision.requires_approval,
    "reversible": decision.reversible,
    "decision_id": decision.decision_id,
    "trace_id": decision.trace_id,
}, indent=2))
```

```text
{
  "verb": "act",
  "reason_code": "policy_rule",
  "action_id": "pay",
  "confidence": 0.95,
  "score": 0.8475,
  "requires_approval": true,
  "reversible": false,
  "decision_id": "DEC-...",
  "trace_id": "TRC-..."
}
```

The default action policy selects `pay` and flags the approval. The host must obtain that approval
before it executes `pay`. The policy uses one utility score and the approval flag; it does not weigh
the promise or the attention budget separately. The [live composite
planner](#the-live-composite-planner) below uses the same request with a planner that does.

The full record is in [the decision contract](docs/02-core/01-contract/01-decision-contract.md).
The same shape works for signal attention, policies, planners and the live composite planner.

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.10.0#subdirectory=packages/python/laix"
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
See the [quickstart](docs/01-start/02-first-steps/01-quickstart.md) for the full setup.

## Why LAIX

- **The decision is explicit.** Every decision carries a verb, a reason code, confidence, a score
  and a trace. The app branches on the reason code, not on prose.
- **The next decision starts from the current state.** Commitments, human-attention budget, approvals,
  revisions, receipts and outcomes carry forward. A decision is a step, not a snapshot.
- **The host keeps control.** The core is stateless. The host owns execution, data, storage and
  delivery; the optional app kit adds the lifecycle around the decision.

## How it works

![How LAIX works: an agent plans, LAIX decides, the host executes, and the outcome returns as the next decision](docs/assets/how-it-works.svg)

An agent or automation plans the task. LAIX decides the next move. The host executes it. The
receipt and outcome close the loop and calibrate the next decision.

The core is `DecisionRequest` in, `Decision` out. A policy can be a rule set, a learned policy or a
planner behind `PlannerPolicy`. The app kit is optional; it adds execution, records, stores,
streaming, delivery and bench.

## The live composite planner

**Live** means the decision is made inside the running loop, at event time, with the current state.
The core stays stateless: the host supplies commitments, budget, approvals and execution state with
each request.

`LiveCompositePlanner` is a planner, not a second entry point. **Composite** means it combines four
scores: utility, promises, execution risk and human attention. It returns a `PlannerResult`;
`PlannerPolicy` adapts that result to the public `Decision`. The host still calls `decide`, and still
gets a `Decision`.

The same payment request from [One decision](#one-decision), with a different policy:

```python
import json

from laix import LiveCompositePlanner, PlannerPolicy, decide

# request is the same DecisionRequest built in "One decision".
policy = PlannerPolicy(LiveCompositePlanner(), name="live.v1")
decision = decide(request, policy=policy)[0]

print(decision.action_id, decision.reason_code, decision.score)
print(json.dumps({
    "utility": decision.attributes["utility"],
    "commitment": decision.attributes["commitment_score"],
    "execution": decision.attributes["execution_score"],
    "human_attention": decision.attributes["human_attention_score"],
}, indent=2))
```

```text
ask live_decision 1.09
{
  "utility": 0.57,
  "commitment": 0.6,
  "execution": -0.0,
  "human_attention": -0.08
}
```

The composite planner chooses `ask` over `pay`. `pay` has the higher utility, but it breaks the
commitment to ask the owner before paying; `ask` fulfills that commitment and stays within the
human-attention budget. The decision carries the four scores, so the trade-off is visible.

| Same request | Policy | Result |
|---|---|---|
| `decide(request)` | `ActionPolicy` (default) | `pay`; approval required |
| `decide(request, policy=...)` | `PlannerPolicy(LiveCompositePlanner())` | `ask`; commitment `c1` fulfilled |

`decide` is the public entry point. `LiveCompositePlanner` is one chooser behind it. `PlannerPolicy`
is the adapter that makes a planner return the public `Decision`. They are layers, not alternatives.

A separate conflict scenario is in [`examples/python/03-plan/conflict_scenario.py`](examples/python/03-plan/conflict_scenario.py).

## Decision continuity

A decision is one step in a sequence. It leaves state for the next decision.

| Step | Decision | State carried forward |
|---|---|---|
| 1 | acts, creating commitment `c1` | `c1` open; human-attention budget 0.6 spent |
| 2 | asks because `c1` is due and the budget is low | `c1` still open; approval pending |
| 3 | verifies after execution | `c1` fulfilled; receipt and outcome recorded |

The next decision sees the commitments, human-attention budget, approvals, revisions and outcomes the
previous one left. See [Decision continuity](docs/02-core/04-continuity/01-decision-continuity.md).

In a 12-episode synthetic mechanism test, the stateful runtime completed **100%** of episodes; a
stateless utility planner completed **0%** with 36 continuity errors. See the
[continuity benchmark](docs/06-research/02-evaluation/continuity-benchmark.md).

## Where it fits

| System | Owns |
|---|---|
| Agent framework | Orchestration, tools, memory and the model loop. |
| Workflow engine | Durable execution, retries and process state. |
| **LAIX** | The decision, its reason, approval, audit trail and continuity. |

LAIX sits inside the host. It does not replace the agent framework or the workflow engine; it makes
the decision inside one task explicit and auditable. For a fair comparison with JEV, classifiers and
judges, see [LAIX and decision models](docs/04-concepts/02-positioning/01-decision-models.md).

Robotics: task-level decisions above the safety and motion layer. See
[LAIX for robotics](docs/04-concepts/02-positioning/03-robotics.md).

## When to use LAIX

| Situation | Use |
|---|---|
| One app with one simple rule | Plain app code, or a small policy. |
| Several agents, tasks or decision classes need one contract | LAIX core. |
| You need approval, audit, execution receipts or continuity | LAIX core plus the app kit. |
| You need orchestration, tools and memory | An agent framework, with LAIX inside it. |
| You need durable execution and retries | A workflow engine, with LAIX deciding. |
| You only need a classifier or a judge | A model; LAIX can wrap it behind `PlannerPolicy`. |

## Results

`LiveCompositePlanner` scores **30/30** on the frozen 30-case test split of the 120-case corpus and
**6/6** on the conflict cases. The hand-built glue baseline scores 28/30; the **+6.7 pp** difference
is **not yet significant** (p = 0.48). Every single-concern planner has significantly lower accuracy
(McNemar p ≤ 0.008).

![Accuracy and conflict accuracy on the frozen test split](docs/assets/benchmark.png)

| Measure | `LiveCompositePlanner` | Best comparator |
|---|---:|---:|
| Accuracy, all 30 cases | **100%** | 93.3% (glue baseline) |
| Conflict accuracy, 6 cases | **100%** | 100% (glue baseline) |
| Promise keeping | **100%** | 100% (glue baseline) |
| Irreversible actions | **0%** | 0% (glue baseline) |
| Human-attention-budget violations | **0%** | 0% (glue baseline) |
| p95 decision latency | **0.22 ms** | — |

The glue baseline matches `LiveCompositePlanner` on conflict, promises, reversibility and budget. The
remaining difference is accuracy on the other 24 cases, and it is not significant on 30 cases.

On a 10-task τ-bench retail slice, the LAIX guardrail passed **10/10** vs **9/10** for the baseline
(single trial). See [τ-bench](docs/06-research/02-evaluation/tau-bench.md).

External validation — real incident replay or a participant study — is still pending. The full
ablation, the test matrix and the evidence caveats are in
[the benchmark](docs/06-research/02-evaluation/benchmark.md) and
[the evidence map](docs/06-research/02-evaluation/evidence-map.md).

## Documentation

| Start with | Covers |
|---|---|
| [Documentation index](docs/README.md) | every guide and reference page |
| [Quickstart](docs/01-start/02-first-steps/01-quickstart.md) | install and first decision |
| [Core overview](docs/02-core/README.md) | contract, policies, planners, continuity, learning |
| [App-kit overview](docs/03-appkit/README.md) | execution, streams, stores, platform, delivery, bench |
| [Decision lifecycle](docs/01-start/01-orientation/02-decision-lifecycle.md) | moment to outcome in one loop |
| [Deployment](docs/03-appkit/05-operate/03-deployment.md) | production topology, reliability, rollout and retention |
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
links. See [Testing](docs/05-project/02-quality/01-testing.md) for every check.

For setup, design rules and the pull-request checklist, read [CONTRIBUTING.md](CONTRIBUTING.md).
Questions go to [SUPPORT.md](SUPPORT.md); participation is covered by
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately through [SECURITY.md](SECURITY.md); the
[security and threat model](docs/04-concepts/03-trust/01-security.md) explains the boundaries.

## Citation

If you use LAIX in research, cite it via [CITATION.cff](CITATION.cff).

## License

Apache-2.0. See [LICENSE](LICENSE). Current release: `0.10.0`.
