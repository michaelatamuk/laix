![LAIX — Live Decision for AI agents, between plan and execution](docs/assets/banner.png)

[![CI](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelatamuk/laix/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![Node 22+](https://img.shields.io/badge/node-22%2B-339933?logo=node.js&logoColor=white)

# LAIX — Live AI Experience

**LAIX makes the live decision for AI agents that act in the real world.**

Agent frameworks plan. Workflow engines orchestrate. LAIX sits between the plan and its execution:
it decides whether to wait, observe, guide, ask, act, verify or escalate — explicitly, with a reason
code, a score and an audit trail. It is not an agent framework, a workflow engine or a model.

One contract for utility, commitments, execution risk and human attention, with **decision
continuity**: each decision carries its commitments, attention budget, approvals and revisions into
the next. The host owns execution, data, delivery and storage; LAIX owns the decision and its trail.
LAIX is **training-free**: the default path is deterministic policies and planners; a planner can use
a model the host supplies.

**Who it is for:** teams building AI agents or automations that take real actions — especially when
approvals, promises, human attention or auditability matter.

**Status:** pre-1.0 (`0.17.2`). Internal benchmarks and a synthetic continuity test; external
validation pending.

[Quickstart](docs/01-start/02-first-steps/01-quickstart.md) ·
[Documentation](docs/README.md) ·
[Examples](examples/README.md) ·
[Issues](https://github.com/michaelatamuk/laix/issues)

## Why LAIX

- **The decision is explicit.** Every decision carries a verb, a reason code, confidence, a score
  and a trace. The app branches on the reason code, not on prose.
- **The next decision starts from the current state.** Commitments (promises), human-attention budget
  (how much you can interrupt a person), approvals, revisions, execution receipts and measured outcomes
  carry forward. A decision is a step, not a snapshot.
- **Promises can cross owners.** A `CommitmentGraph` combines the local ledger with other parties'
  commitments, so the planner can require an external dependency to be verified before an action that
  depends on it.
- **The host keeps control.** The decision layer is stateless. The host owns execution, data, storage
  and delivery; the optional app kit adds the lifecycle around the decision.
- **It is portable and testable.** Python uses the standard library only. TypeScript mirrors the same
  contract, and CI checks parity, conformance, examples and the benchmark.

## When to use LAIX

| You need | Use |
|---|---|
| Planning, tools and memory | An agent framework, with LAIX inside it. |
| Long-running execution, retries and process state | A workflow engine, with LAIX deciding. |
| One explicit decision with reason, approval, audit trail and continuity | LAIX. |
| One app with one simple rule | Plain app code, or one small decision rule. |
| A classifier or a judge | A model; LAIX can wrap it behind the same contract. |

LAIX sits inside the host; it does not replace the agent framework or workflow engine. For a fair
comparison with decision models, classifiers and judges, see
[LAIX and decision models](docs/04-concepts/02-positioning/01-decision-models.md).

Robotics: task-level decisions above the safety and motion layer. See
[LAIX for robotics](docs/04-concepts/02-positioning/03-robotics.md).

## Install

Python:

```powershell
pip install "git+https://github.com/michaelatamuk/laix.git@v0.17.2#subdirectory=packages/python/laix"
```

From a local checkout, at the repository root:

```powershell
pip install -e packages/python/laix
```

TypeScript, from a local checkout (the package is not published to npm yet):

```powershell
npm install file:../path/to/laix/packages/typescript/laix
```

Python 3.11+ or Node 22+. See the [quickstart](docs/01-start/02-first-steps/01-quickstart.md) for the
full setup.

## One decision

A `DecisionRequest` carries what the app knows and the options it can take. `decide` returns one
`Decision`. In this example a payment needs owner approval: the built-in action policy chooses to
pay and flags the approval, and the host must obtain that approval before it executes.

```python
from laix import ActionOption, Belief, DecisionRequest, Situation, decide

request = DecisionRequest(
    subject="invoice 4832",
    at="2026-11-01T10:00:00+00:00",
    situation=Situation(          # what the app knows
        id="s-1",
        at="2026-11-01T10:00:00+00:00",
        subject="invoice 4832",
        beliefs=(
            Belief(                # one claim and its confidence
                id="b-1",
                proposition="the invoice matches the work order",
                confidence=0.95,
            ),
        ),
        attributes={"urgency": 0.8},  # app-provided context
    ),
    options=(
        ActionOption(
            id="pay",
            verb="act",
            name="pay the invoice",
            expected_benefit=0.95,   # expected gain
            risk=0.05,               # estimated downside
            requires_approval=True,  # a person must approve
            reversible=False,        # cannot be undone
        ),
        ActionOption(
            id="wait",
            verb="wait",
            name="wait for the next review",
            expected_benefit=0.2,
        ),
    ),
)

decision = decide(request)[0]  # decide returns a list
print(decision.verb, decision.reason_code, decision.action_id, decision.requires_approval)
```

```text
act policy_rule pay True
```

`act` is the chosen verb (do it now), `pay` is the chosen option, and `True` means a person must
approve before the host executes. `policy_rule` is the reason code: a built-in policy rule made the
choice.

The full request, with a commitment and a human-attention budget, is in the
[quickstart](docs/01-start/02-first-steps/01-quickstart.md#full-request-approval-commitment-and-attention).
TypeScript has the same `Decision` shape; the quickstart has the TypeScript version.

## How it works

![How LAIX works: an agent plans, LAIX decides, the host executes, and the outcome returns as the next decision](docs/assets/how-it-works.svg)

An agent or automation plans the task. LAIX decides the next move. The host executes it. The receipt
and outcome close the loop and calibrate the next decision.

The decision layer is `DecisionRequest` in, `Decision` out. The app kit is optional; it adds
execution, records, stores, streaming, delivery and bench.

## The decision surface

The same contract covers attention, action, several decision shapes and your own policy.

| What you get | In one line |
|---|---|
| [Seven verbs](docs/02-decision/01-contract/01-decision-contract.md) | `wait`, `observe` (gather evidence), `guide` (surface attention), `ask`, `act` (do it now), `verify`, `escalate` |
| [Two decision families](docs/02-decision/README.md) | signal attention — what matters now — and action — what to do |
| [Five decision shapes](docs/02-decision/03-decision-shapes/README.md) | single (one choice), sequence (a chain), fleet (many pending), history (repair), explain (why and what would flip it) |
| [Bring your own policy](docs/02-decision/03-decision-shapes/01-single/05-policies.md) | any `name` + `decide` object; a planner or model behind the same contract |
| [Portable and tested](docs/06-project/02-quality/01-testing.md) | Python standard library only; TypeScript parity checked in CI |
| [Integrations](docs/03-appkit/01-build/README.md) | [LangGraph](docs/03-appkit/01-build/04-langgraph.md), [MCP](docs/03-appkit/01-build/05-mcp.md), [A2A and OpenAPI](docs/03-appkit/01-build/06-a2a.md) |

A policy is any object with a `name` and a `decide(request)` method. `PlannerPolicy` adapts a
planner, so a learned policy or model can sit behind the same contract.

## The live composite planner

**Live** means the decision is made inside the running loop, at event time, with the current state.
The decision layer stays stateless: the host supplies commitments, attention budget, approvals and
execution state with each request.

`LiveCompositePlanner` combines four scores: utility (benefit versus cost), commitments, execution risk
and human attention. `PlannerPolicy` adapts its result to the public `Decision`, so the app still
calls `decide` and still gets a `Decision`.

Using the full invoice request from the quickstart (the one with a commitment and a human-attention
budget):

| Same request | Policy | Result |
|---|---|---|
| `decide(request)` | The built-in action policy | `pay`; approval required |
| `decide(request, policy=...)` | `PlannerPolicy(LiveCompositePlanner())` | `ask`; commitment to ask fulfilled |

The composite planner chooses `ask` over `pay`. `pay` has the higher utility, but it breaks the
commitment to ask the owner before paying; `ask` fulfills that commitment and stays within the
human-attention budget. The decision carries the four scores, so the trade-off is visible.

A separate conflict scenario is in
[`examples/python/decision/decision/history/conflict_scenario.py`](examples/python/decision/decision/history/conflict_scenario.py).

## Decision continuity

A decision is one step in a sequence. It leaves state for the next decision.

| Step | Decision | State carried forward |
|---|---|---|
| 1 | acts, creating commitment `c1` | `c1` open; human-attention budget 0.6 spent |
| 2 | asks because `c1` is due and the budget is low | `c1` still open; approval pending |
| 3 | verifies after execution | `c1` fulfilled; receipt and outcome recorded |

The next decision sees the commitments, human-attention budget, approvals, revisions and outcomes the
previous one left. See [Decision continuity](docs/02-decision/03-decision-shapes/04-history.md).

In a 12-episode synthetic mechanism test, the stateful decision loop completed **100%** of episodes; a
stateless utility planner completed **0%** with 36 continuity errors. See the
[continuity benchmark](docs/07-research/02-evaluation/continuity-benchmark.md).

## Results

`LiveCompositePlanner` scores **30/30** on the frozen 30-case test split of the 120-case corpus and
**6/6** on the conflict cases. The hand-built integration baseline (the “glue baseline”) scores 28/30; the **+6.7 pp** difference
is **not yet significant** (p = 0.48). Every single-concern planner has significantly lower accuracy
(McNemar p ≤ 0.008).

![Accuracy and conflict accuracy on the frozen test split](docs/assets/benchmark.png)

| Measure | `LiveCompositePlanner` | Best comparator |
|---|---:|---:|
| Accuracy, all 30 cases | **100%** | 93.3% (glue baseline) |
| Conflict accuracy, 6 cases | **100%** | 100% (glue baseline) |
| Promise keeping | **100%** | 100% (glue baseline) |
| Irreversible actions | **0%** | 0% (glue baseline) |
| p95 decision latency | **0.22 ms** | — |

The glue baseline matches on conflict, promises, reversibility and budget; the remaining gap is
accuracy on the other 24 cases.

On a 10-task τ-bench retail slice, the guardrail passed **10/10** vs **9/10** for the baseline
(single trial). External validation is still pending; full evidence and caveats are in
[the benchmark](docs/07-research/02-evaluation/benchmark.md) and
[the evidence map](docs/07-research/02-evaluation/evidence-map.md).

## Documentation

| Start with | Covers |
|---|---|
| [Documentation index](docs/README.md) | every guide and reference page |
| [Quickstart](docs/01-start/02-first-steps/01-quickstart.md) | install and first decision |
| [Decision overview](docs/02-decision/README.md) | contract, domain, decision shapes, sensing, learning, evaluation |
| [Decision shapes](docs/02-decision/03-decision-shapes/README.md) | single, sequence, fleet, history and explain |
| [App-kit overview](docs/03-appkit/README.md) | execution, streams, stores, platform, delivery, bench |
| [Decision lifecycle](docs/01-start/01-orientation/02-decision-lifecycle.md) | moment to outcome in one loop |
| [Deployment](docs/03-appkit/05-operate/03-deployment.md) | production topology, reliability, rollout and retention |
| [LangGraph](docs/03-appkit/01-build/04-langgraph.md) | a decision node, approval interrupt and checkpointer |
| [MCP server](docs/03-appkit/01-build/05-mcp.md) | expose `decide` over stdio |
| [A2A and OpenAPI](docs/03-appkit/01-build/06-a2a.md) | an agent card and a host action profile |
| [Examples](examples/README.md) | Python and TypeScript, grouped by decision and app kit |

## Contributing

Run the full checks before opening a change; the commands, design rules and pull-request checklist
are in [CONTRIBUTING.md](CONTRIBUTING.md). CI runs the same checks on every push, plus the live
benchmark, TypeScript parity, examples, and docs link and anchor checks. See
[Testing](docs/06-project/02-quality/01-testing.md) for every check.

Questions go to [SUPPORT.md](SUPPORT.md); participation is covered by
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately through [SECURITY.md](SECURITY.md); the
[security and threat model](docs/04-concepts/03-trust/01-security.md) explains the boundaries.

## Citation

If you use LAIX in research, cite it via [CITATION.cff](CITATION.cff).

## License

Apache-2.0. See [LICENSE](LICENSE). Current release: `0.17.2`.
