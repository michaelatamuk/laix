# LAIX documentation

LAIX — **Live AI Experience** — is the live decision runtime for AI agents and automations that act in
the real world. An agent or automation is always in the loop: it notices what is changing, decides what
matters and acts before the moment passes. LAIX gives that loop a single decision contract. The host
owns the experience; LAIX owns the decision.

> **What matters now, and what should the experience do about it?**

LAIX turns what is happening, the options the host can offer and the limits the host sets into one
decision.

Numbered sections are read in order. Concepts and Project are reference sections and stay
unnumbered.

## Start here

| Page | Answers |
|---|---|
| [What is LAIX?](01-start/01-what-is-laix.md) | What problem does it solve, in plain language? |
| [Quickstart](01-start/02-quickstart.md) | How do I install it and make one decision? |
| [Decision lifecycle](01-start/03-decision-lifecycle.md) | How one decision moves from moment to outcome? |
| [Host integration](01-start/04-host-integration.md) | Where does LAIX plug in, and what does the host keep? |

## Core

Read in order.

| Page | Covers |
|---|---|
| [Core overview](02-core/00-overview.md) | the five layers, the decision loop and the reading map |
| [Decision contract](02-core/01-decision-contract.md) | `DecisionRequest`, `Decision`, the seven verbs and reason codes |
| [Records and schema](02-core/02-records-and-schema.md) | the ten schema records, JSON, versions and change rules |
| [Dispatch](02-core/03-dispatch.md) | `decide`, automatic path selection, ids and confidence provenance |
| [Commitments](02-core/05-commitments.md) | promises, ledgers, due times, dependencies and `PlanningPolicy` |
| [Resources](02-core/11-resources.md) | `Budget`, `ResourceScheduler` and sensing options |
| [Signal attention](02-core/04-signal-attention.md) | the gate pipeline, score, reason codes and the attention scope |
| [Policies](02-core/06-policies.md) | the policy contract, built-in action policy, eight decision-class policies and wrappers |
| [Planner contract](02-core/07-planning/00-planner-contract.md) | `DecisionProblem`, `Plan`, `DecisionEngine`, `EnginePolicy` and the simulator |
| [Live planners](02-core/07-planning/01-live-planners.md) | utility, commitment, execution-risk and human-attention scoring |
| [Live decision engine](02-core/07-planning/02-live-decision-engine.md) | `LiveDecisionEngine`, `CompositeScore` and the combined plan |
| [Model-based planners](02-core/07-planning/03-model-based-planners.md) | `MDPPlanner`, `POMDPPlanner`, value iteration and belief update |
| [Outcome learning](02-core/08-outcome-learning.md) | outcomes, rewards, `UCBBandit`, causal attribution and attention outcomes |
| [Calibration and model learning](02-core/09-calibration-and-model-learning.md) | prediction and decision calibration, `CalibratedPolicy` and `ModelLearner` |
| [Decision continuity](02-core/10-decision-continuity.md) | what carries from one decision to the next and the continuity benchmark |
| [Evaluation](02-core/12-evaluation.md) | cases, reports, the live decision bench and LAIX-Bench |
| [Foundation](02-core/13-foundation.md) | perception records and the shared support helpers |

## App kit

| Page | Covers |
|---|---|
| [App-kit architecture](03-appkit/00-architecture.md) | surface, runtime, state, result, ports and proof |
| [Integration](03-appkit/01-integration.md) | adapters, confidence, rollout and custom policies |
| [Streaming](03-appkit/02-streaming.md) | event time, cadence, backpressure, checkpoints, timeline and sources |
| [Live Context](03-appkit/03-live-context.md) | detectors, admission and frames |
| [Execution](03-appkit/04-execution.md) | receipts, idempotency, multi-step recovery, records |
| [Stores](03-appkit/05-stores.md) | state, checkpoints, commitments and outcomes |
| [Platform](03-appkit/06-platform.md) | skills, events and approvals |
| [Delivery](03-appkit/07-delivery.md) | ports, receipts and the host transport |
| [LAIX-Bench](03-appkit/08-laix-bench.md) | LAIX-Bench, stream bench and planner simulation |
| [Metrics](03-appkit/09-metrics.md) | stream counters, Prometheus and latency |
| [Deployment](03-appkit/10-deployment.md) | production topology, reliability, observability, rollout and retention |

## Concepts

| Page | Answers |
|---|---|
| [System architecture](04-concepts/system-architecture.md) | how the whole system fits together |
| [Scope and boundaries](04-concepts/scope-and-boundaries.md) | where PPMA, LAIX, core, app kit and host end |
| [Decision models](04-concepts/decision-models.md) | how LAIX relates to judgment and decision models |
| [PPMA integration](04-concepts/ppma-integration.md) | why and how PPMA would use LAIX |
| [Privacy](04-concepts/privacy.md) | what may be shared, stored or exported |
| [Security](04-concepts/security.md) | trust boundaries, threats and controls |
| [FAQ](04-concepts/faq.md) | models, execution, novelty and when to use LAIX |
| [Glossary](04-concepts/glossary.md) | the vocabulary used across the docs |

## Project

| Page | Covers |
|---|---|
| [Repository structure](05-project/repository-structure.md) | where each package, module and test lives |
| [Testing](05-project/testing.md) | pytest, ruff, tsc, bench, conformance and CI |
| [Troubleshooting](05-project/troubleshooting.md) | symptoms, reason codes, execution failures and performance |
| [Migration](05-project/migration.md) | upgrades, compatibility, deprecation and data migration |
| [API map](05-project/api-map.md) | public classes and functions by role |
| [Versioning](05-project/versioning.md) | package, schema and vector versions |
| [Roadmap](05-project/roadmap.md) | what is done and what is next |
| [Brand assets](assets/README.md) | logo, banner, architecture and demo placeholder |

## Research and evidence

| Page | Covers |
|---|---|
| [Research and evidence](06-research/README.md) | claim, prior-art gap, experiments, validation and paper plan |

## Community

| Page | Covers |
|---|---|
| [Contributing](../CONTRIBUTING.md) | setup, design rules, checks and the pull-request workflow |
| [Security](../SECURITY.md) | vulnerability reporting and supported versions |
| [Support](../SUPPORT.md) | where to ask and what to include |
| [Code of conduct](../CODE_OF_CONDUCT.md) | participation rules |
| [Citation](../CITATION.cff) | how to cite LAIX |

## Examples

Runnable examples are organized by language and lifecycle in
[`../examples/README.md`](../examples/README.md). Every Python and TypeScript example is run by CI.

## Which page do I need?

| I want to… | Read |
|---|---|
| make one decision | [Quickstart](01-start/02-quickstart.md) |
| plug LAIX into an app | [Host integration](01-start/04-host-integration.md), then [Integration](03-appkit/01-integration.md) |
| write my own policy | [Policies](02-core/06-policies.md) |
| stream events | [Streaming](03-appkit/02-streaming.md) |
| execute and recover | [Execution](03-appkit/04-execution.md) |
| learn from outcomes | [Outcome learning](02-core/08-outcome-learning.md) |
| understand the planner contract | [Planner contract](02-core/07-planning/00-planner-contract.md) |
| see the end-to-end loop | [Decision lifecycle](01-start/03-decision-lifecycle.md) |
| see the public API | [API map](05-project/api-map.md) |
| operate in production | [Deployment](03-appkit/10-deployment.md), [Metrics](03-appkit/09-metrics.md), [Troubleshooting](05-project/troubleshooting.md) |
| troubleshoot a decision | [Troubleshooting](05-project/troubleshooting.md) |
| upgrade a deployment | [Migration](05-project/migration.md) |
| report a vulnerability | [Security](../SECURITY.md) |
| contribute | [Contributing](../CONTRIBUTING.md), then [Testing](05-project/testing.md) |
| check model use or novelty | [FAQ](04-concepts/faq.md), then [Research and evidence](06-research/README.md) |
| look up a term | [Glossary](04-concepts/glossary.md) |
| work on the repository | [Testing](05-project/testing.md), then [Repository structure](05-project/repository-structure.md) |

## Reading paths

| I am… | Start with |
|---|---|
| Product | [What is LAIX?](01-start/01-what-is-laix.md), [Decision lifecycle](01-start/03-decision-lifecycle.md), [Scope and boundaries](04-concepts/scope-and-boundaries.md) |
| Engineer | [Quickstart](01-start/02-quickstart.md), [Decision contract](02-core/01-decision-contract.md), [Policies](02-core/06-policies.md), [Planner contract](02-core/07-planning/00-planner-contract.md), [Live decision engine](02-core/07-planning/02-live-decision-engine.md), [App kit](03-appkit/00-architecture.md) |
| Operator | [Execution](03-appkit/04-execution.md), [Stores](03-appkit/05-stores.md), [Platform](03-appkit/06-platform.md), [Delivery](03-appkit/07-delivery.md), [Deployment](03-appkit/10-deployment.md), [Metrics](03-appkit/09-metrics.md) |
| Contributor | [Contributing](../CONTRIBUTING.md), [Testing](05-project/testing.md), [Repository structure](05-project/repository-structure.md) |
| Researcher or reviewer | [Research and evidence](06-research/README.md), then [Prior art](06-research/01-positioning/prior-art.md), [Benchmark](06-research/02-evaluation/benchmark.md) |
