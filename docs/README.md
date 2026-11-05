# LAIX documentation

LAIX answers one question for a live app: given what is happening, what the app can do and what the
host allows, should it **wait, observe, guide, ask, act, verify or escalate**?

## Start here

| Page | Answers |
|---|---|
| [What is LAIX?](01-start/what-is-laix.md) | What problem does it solve, in plain language? |
| [Quickstart](01-start/quickstart.md) | How do I install it and make one decision? |
| [Host integration](01-start/host-integration.md) | Where does LAIX plug in, and what does the host keep? |

## Core

Read in order.

| Page | Covers |
|---|---|
| [Core architecture](02-core/00-architecture.md) | the core building blocks and how they stack |
| [Decision contract](02-core/01-decision-contract.md) | request, response, records and schema |
| [Attention](02-core/02-attention.md) | task-level attention and its scope |
| [Policies](02-core/03-policies.md) | packaged policies, authoring, planning, group and shadow |
| [Outcome learning](02-core/04-outcome-learning.md) | rewards, UCB, causal attribution, calibration and model learning |
| [Evaluation](02-core/05-evaluation.md) | cases, comparison and parity |
| [Engines](02-core/06-engines.md) | utility, MDP, POMDP, simulation and calibration |

## App kit

| Page | Covers |
|---|---|
| [App-kit architecture](03-appkit/00-architecture.md) | runtime, data, ports and proof tools |
| [Integration](03-appkit/01-integration.md) | adapters, confidence, rollout and custom policies |
| [Streaming](03-appkit/02-streaming.md) | event time, cadence, backpressure, checkpoints and sources |
| [Live Context](03-appkit/03-live-context.md) | detectors, admission and frames |
| [Execution](03-appkit/04-execution.md) | receipts, idempotency, sagas, records and recovery |
| [Stores](03-appkit/05-stores.md) | state, checkpoints, commitments and outcomes |
| [Platform](03-appkit/06-platform.md) | skills, events and approvals |
| [Delivery](03-appkit/07-delivery.md) | ports, receipts and the host transport |
| [Bench](03-appkit/08-bench.md) | LAIX-Bench, stream bench and engine simulation |
| [Metrics](03-appkit/09-metrics.md) | stream counters, Prometheus and latency |

## Concepts

| Page | Answers |
|---|---|
| [Architecture](04-concepts/architecture.md) | how the whole system fits together |
| [Boundaries](04-concepts/boundaries.md) | where PPMA, LAIX, core, app kit and host end |
| [Decision models](04-concepts/decision-models.md) | how LAIX relates to judgment and decision models |
| [PPMA](04-concepts/ppma.md) | why and how PPMA would use LAIX |
| [Privacy](04-concepts/privacy.md) | what may be shared, stored or exported |
| [Glossary](04-concepts/glossary.md) | the vocabulary used across the docs |

## Project

| Page | Covers |
|---|---|
| [Structure](05-project/structure.md) | where each package, module and test lives |
| [Testing](05-project/testing.md) | pytest, ruff, tsc, bench, conformance and CI |
| [Versioning](05-project/versioning.md) | package, schema and vector versions |
| [Roadmap](05-project/roadmap.md) | what is done and what is next |

## Examples

Runnable examples are organized by language and lifecycle in
[`../examples/README.md`](../examples/README.md). Every Python and TypeScript example is run by CI.

## Which page do I need?

| I want to… | Read |
|---|---|
| make one decision | [Quickstart](01-start/quickstart.md) |
| plug LAIX into an app | [Host integration](01-start/host-integration.md), then [Integration](03-appkit/01-integration.md) |
| write my own policy | [Policies](02-core/03-policies.md) |
| stream events | [Streaming](03-appkit/02-streaming.md) |
| execute and recover | [Execution](03-appkit/04-execution.md) |
| learn from outcomes | [Outcome learning](02-core/04-outcome-learning.md) |
| understand the engine contract | [Engines](02-core/06-engines.md) |
| work on the repository | [Testing](05-project/testing.md), then [Structure](05-project/structure.md) |
