# LAIX documentation

LAIX — **Live AI Experience** — is the live decision layer for AI agents that act in
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
| [Start overview](01-start/README.md) | the shortest path from zero to one decision |
| [Orientation](01-start/01-orientation/README.md) | what LAIX is and how one decision moves through the loop |
| [First steps](01-start/02-first-steps/README.md) | install, make one decision and integrate a host |

## Decision

Read in order.

| Page | Covers |
|---|---|
| [Decision overview](02-decision/README.md) | the layers, the decision loop and the reading map |
| [Contract](02-decision/01-contract/README.md) | request, response, planner contract, records and dispatch |
| [Domain](02-decision/02-domain/README.md) | decisions, commitments, outcomes and perception |
| [Decision](02-decision/03-decision-shapes/README.md) | single, sequence, fleet, history and explain |
| [Sensing](02-decision/04-sensing/README.md) | signal attention and resource admission |
| [Learning](02-decision/05-learning/README.md) | calibration, model learning, bandit and causal attribution |
| [Evaluation](02-decision/06-evaluation/README.md) | cases, benchmarks, simulation and continuity |
| [Support](02-decision/07-support/README.md) | schema and support helpers |

## App kit

| Page | Covers |
|---|---|
| [App-kit overview](03-appkit/README.md) | surface, decision loop, execution, ports and proof |
| [Build](03-appkit/01-build/README.md) | adapter, one decision and policy selection |
| [Run](03-appkit/02-run/README.md) | decision loop, streaming and live context |
| [Execute](03-appkit/03-execute/README.md) | execution, recovery, proposals and records |
| [Connect](03-appkit/04-connect/README.md) | stores, platform and delivery |
| [Operate](03-appkit/05-operate/README.md) | bench, metrics and deployment |

## Concepts

| Page | Answers |
|---|---|
| [Concepts overview](04-concepts/README.md) | the ideas behind the contracts |
| [Architecture](04-concepts/01-architecture/README.md) | what LAIX is, how it decides and where its boundary sits |
| [Positioning](04-concepts/02-positioning/README.md) | how LAIX relates to decision models and PPMA |
| [Trust](04-concepts/03-trust/README.md) | security, privacy and the host boundary |
| [Reference](04-concepts/04-reference/README.md) | vocabulary and common questions |

## Project

| Page | Covers |
|---|---|
| [Project overview](05-project/README.md) | the working, release and direction pages |
| [Repository](05-project/01-repository/README.md) | structure and the public API map |
| [Quality](05-project/02-quality/README.md) | testing, CI and troubleshooting |
| [Release](05-project/03-release/README.md) | versioning, migration and deprecation |
| [Direction](05-project/04-direction/README.md) | roadmap and adoption |
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

Runnable examples are organized by language, then by decision or app kit, and by decision shape inside the decision layer in [`../examples/README.md`](../examples/README.md). Every Python and TypeScript example is run by CI.

## Which page do I need?

| I want to… | Read |
|---|---|
| make one decision | [Quickstart](01-start/02-first-steps/01-quickstart.md) |
| plug LAIX into an app | [Host integration](01-start/02-first-steps/02-host-integration.md), then [Integration](03-appkit/01-build/01-integration.md) |
| integrate with LangGraph | [LangGraph](03-appkit/01-build/04-langgraph.md) |
| expose decisions over MCP | [MCP server](03-appkit/01-build/05-mcp.md) |
| publish an A2A card or action profile | [A2A and OpenAPI](03-appkit/01-build/06-a2a.md) |
| write my own policy | [Policies](02-decision/03-decision-shapes/01-single/05-policies.md), [Policies in the app](03-appkit/01-build/03-policies-in-the-app.md) |
| stream events | [Streaming](03-appkit/02-run/02-streaming.md) |
| execute and recover | [Execution and recovery](03-appkit/03-execute/01-execution-and-recovery.md) |
| learn from outcomes | [Outcome learning](02-decision/02-domain/03-outcomes.md) |
| understand the planner contract | [Planner contract](02-decision/01-contract/02-planner-contract.md) |
| see the end-to-end loop | [Decision lifecycle](01-start/01-orientation/02-decision-lifecycle.md) |
| see the public API | [API map](05-project/01-repository/02-api-map.md) |
| operate in production | [Deployment](03-appkit/05-operate/03-deployment.md), [Metrics](03-appkit/05-operate/02-metrics.md), [Troubleshooting](05-project/02-quality/02-troubleshooting.md) |
| troubleshoot a decision | [Troubleshooting](05-project/02-quality/02-troubleshooting.md) |
| upgrade a deployment | [Migration](05-project/03-release/02-migration.md) |
| publish a release | [Publishing](05-project/03-release/03-publishing.md) |
| report a vulnerability | [Security](../SECURITY.md) |
| contribute | [Contributing](../CONTRIBUTING.md), then [Testing](05-project/02-quality/01-testing.md) |
| check model use or novelty | [FAQ](04-concepts/04-reference/02-faq.md), then [Research and evidence](06-research/README.md) |
| look up a term | [Glossary](04-concepts/04-reference/01-glossary.md) |
| work on the repository | [Testing](05-project/02-quality/01-testing.md), then [Repository structure](05-project/01-repository/01-repository-structure.md) |

## Reading paths

| I am… | Start with |
|---|---|
| Product | [What is LAIX?](01-start/01-orientation/01-what-is-laix.md), [Decision lifecycle](01-start/01-orientation/02-decision-lifecycle.md), [Scope and boundaries](04-concepts/01-architecture/02-scope-and-boundaries.md) |
| Engineer | [Quickstart](01-start/02-first-steps/01-quickstart.md), [Decision contract](02-decision/01-contract/01-decision-contract.md), [Policies](02-decision/03-decision-shapes/01-single/05-policies.md), [Planner contract](02-decision/01-contract/02-planner-contract.md), [Live composite planner](02-decision/03-decision-shapes/01-single/02-composite.md), [App kit](03-appkit/README.md) |
| Operator | [Execution and recovery](03-appkit/03-execute/01-execution-and-recovery.md), [Stores](03-appkit/04-connect/01-stores.md), [Platform](03-appkit/04-connect/02-platform.md), [Delivery](03-appkit/04-connect/03-delivery.md), [Deployment](03-appkit/05-operate/03-deployment.md), [Metrics](03-appkit/05-operate/02-metrics.md) |
| Contributor | [Contributing](../CONTRIBUTING.md), [Testing](05-project/02-quality/01-testing.md), [Repository structure](05-project/01-repository/01-repository-structure.md) |
| Researcher or reviewer | [Research and evidence](06-research/README.md), then [Prior art](06-research/01-positioning/prior-art.md), [Benchmark](06-research/02-evaluation/benchmark.md) |
