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
| [Core overview](02-core/README.md) | the five layers, the decision loop and the reading map |
| [Contract](02-core/01-contract/README.md) | request, response, records, schema and dispatch |
| [Decide](02-core/02-decide/README.md) | signal attention, commitments, policies and resources |
| [Planning](02-core/03-planning/README.md) | planner contract, live planners, live engine and model-based planners |
| [Continuity](02-core/04-continuity/README.md) | decision continuity and the continuity benchmark |
| [Learning](02-core/05-learning/README.md) | outcomes, rewards, calibration and model learning |
| [Reference](02-core/06-reference/README.md) | evaluation and foundation |

## App kit

| Page | Covers |
|---|---|
| [App-kit overview](03-appkit/README.md) | surface, runtime, execution, ports and proof |
| [Build](03-appkit/01-build/README.md) | adapter, one decision and policy selection |
| [Run](03-appkit/02-run/README.md) | decision runtime, streaming and live context |
| [Execute](03-appkit/03-execute/README.md) | execution, recovery, proposals and records |
| [Connect](03-appkit/04-connect/README.md) | stores, platform and delivery |
| [Operate](03-appkit/05-operate/README.md) | bench, metrics and deployment |

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
| [Adoption plan](05-project/adoption-plan.md) | benchmarks, design partners, distribution, compliance and the first wedge |
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
| plug LAIX into an app | [Host integration](01-start/04-host-integration.md), then [Integration](03-appkit/01-build/01-integration.md) |
| write my own policy | [Policies](02-core/02-decide/03-policies.md), [Policies in the app](03-appkit/01-build/03-policies-in-the-app.md) |
| stream events | [Streaming](03-appkit/02-run/02-streaming.md) |
| execute and recover | [Execution and recovery](03-appkit/03-execute/01-execution-and-recovery.md) |
| learn from outcomes | [Outcome learning](02-core/05-learning/01-outcome-learning.md) |
| understand the planner contract | [Planner contract](02-core/03-planning/01-planner-contract.md) |
| see the end-to-end loop | [Decision lifecycle](01-start/03-decision-lifecycle.md) |
| see the public API | [API map](05-project/api-map.md) |
| operate in production | [Deployment](03-appkit/05-operate/03-deployment.md), [Metrics](03-appkit/05-operate/02-metrics.md), [Troubleshooting](05-project/troubleshooting.md) |
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
| Engineer | [Quickstart](01-start/02-quickstart.md), [Decision contract](02-core/01-contract/01-decision-contract.md), [Policies](02-core/02-decide/03-policies.md), [Planner contract](02-core/03-planning/01-planner-contract.md), [Live decision engine](02-core/03-planning/03-live-decision-engine.md), [App kit](03-appkit/README.md) |
| Operator | [Execution and recovery](03-appkit/03-execute/01-execution-and-recovery.md), [Stores](03-appkit/04-connect/01-stores.md), [Platform](03-appkit/04-connect/02-platform.md), [Delivery](03-appkit/04-connect/03-delivery.md), [Deployment](03-appkit/05-operate/03-deployment.md), [Metrics](03-appkit/05-operate/02-metrics.md) |
| Contributor | [Contributing](../CONTRIBUTING.md), [Testing](05-project/testing.md), [Repository structure](05-project/repository-structure.md) |
| Researcher or reviewer | [Research and evidence](06-research/README.md), then [Prior art](06-research/01-positioning/prior-art.md), [Benchmark](06-research/02-evaluation/benchmark.md) |
