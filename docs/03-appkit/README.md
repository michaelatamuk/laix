# App-kit overview

The core turns one request into one decision. The app kit is the optional layer that turns that
decision into an app: it builds the request, runs the decision loop, executes the action, connects the
host's storage and platform, and proves the result.

Four things define the app kit:

- **One decision.** `Layer` runs the core, and can execute, record and deliver the result.
- **A runtime loop.** `DecisionRuntime` links observation, state, policy, execution and outcome.
- **A stream.** `StreamSession` keeps event time, cadence, buffers, revisions and checkpoints.
- **A host boundary.** Stores, platform and delivery are ports. The host owns the database, the
  credentials and the transport.

The core stays stateless. The app kit adds the surfaces, execution, ports and proof around it.

## The five stages

```mermaid
block-beta
    columns 1

    block:build
        columns 4
        build_label["Build"]
        adapter["Adapter<br/>event → request"]
        layer["Layer<br/>one decision"]
        policies["Policies<br/>select · version · shadow"]
    end

    block:run
        columns 4
        run_label["Run"]
        runtime["DecisionRuntime<br/>observe · decide · measure"]
        stream["StreamSession<br/>event time · revisions"]
        live["LiveContext<br/>detectors · frames"]
    end

    block:execute
        columns 3
        execute_label["Execute"]
        execution["ExecutionBridge · Saga<br/>approve · act · recover"]
        records["Proposal · DecisionRecord<br/>approve · apply · audit"]
    end

    block:connect
        columns 4
        connect_label["Connect"]
        stores["Stores<br/>state · checkpoints · commitments · outcomes"]
        platform["Platform<br/>skills · events · approvals"]
        delivery["Delivery<br/>channel · receipt"]
    end

    block:operate
        columns 4
        operate_label["Operate"]
        bench["Bench<br/>cases · suites"]
        metrics["Metrics<br/>counters · latency"]
        deploy["Deployment<br/>topology · rollout · retention"]
    end

    style build_label fill:transparent,stroke:transparent,font-size:22px,font-weight:bold
    style run_label fill:transparent,stroke:transparent,font-size:14px,font-weight:bold
    style execute_label fill:transparent,stroke:transparent,font-size:14px,font-weight:bold
    style connect_label fill:transparent,stroke:transparent,font-size:14px,font-weight:bold
    style operate_label fill:transparent,stroke:transparent,font-size:14px,font-weight:bold
```

| Stage | Question | Pages |
|---|---|---|
| **Build** | How does the host call LAIX, get one decision and choose a policy? | [Integration](01-build/01-integration.md), [Single decision](01-build/02-single-decision.md), [Policies in the app](01-build/03-policies-in-the-app.md) |
| **Run** | What runs over time and before the choice? | [Decision runtime](02-run/01-decision-runtime.md), [Streaming](02-run/02-streaming.md), [Live Context](02-run/03-live-context.md) |
| **Execute** | What happens after the choice? | [Execution and recovery](03-execute/01-execution-and-recovery.md), [Proposals and records](03-execute/02-proposals-and-records.md) |
| **Connect** | What does the host supply? | [Stores](04-connect/01-stores.md), [Platform](04-connect/02-platform.md), [Delivery](04-connect/03-delivery.md) |
| **Operate** | How is it proved and run in production? | [Bench](05-operate/01-bench.md), [Metrics](05-operate/02-metrics.md), [Deployment](05-operate/03-deployment.md) |

## What the app kit adds

| Stage | Contract | What it does |
|---|---|---|
| Build | `Layer` | Decides, executes, measures and delivers one decision. |
| Build | `PolicyRegistry` | Registers the policies a layer can select. |
| Run | `DecisionRuntime` | Links observation, state, policy, execution and outcome. |
| Run | `StreamSession` | Turns a stream of events into decisions over time. |
| Run | `LiveContext` | Runs detectors and returns a frame. |
| Execute | `ExecutionBridge` | Checks approval, enforces idempotency, calls a skill and records a receipt. |
| Execute | `Saga` | Compensates completed steps when a later step fails. |
| Execute | `Proposal` | The approval lifecycle for an action that needs a person. |
| Execute | `DecisionRecord` | The audit lifecycle around a decision. |
| Connect | `StateStore` | Saves and loads live state. |
| Connect | `StreamCheckpointStore` | Saves and resumes a stream. |
| Connect | `Platform` | Runs skills, approvals, state and events. |
| Connect | `DeliveryPort` | Delivers a decision and returns a receipt. |
| Operate | `BenchReport` | Runs deterministic cases and suites. |
| Operate | `StreamStats` | Exports stream counters and latency. |
| Operate | `Simulator` | Runs planners in a model and reports the optimality gap. |

The records that cross those stages:

| Contract | What it records |
|---|---|
| `ExperienceState` | Goal, phase, beliefs, open items and expiry. |
| `Proposal` | Pending, approved, rejected, applied and undone. |
| `DecisionRecord` | Draft, approval, execution, undo and verification. |
| `Outcome` | What was measured after a decision. |
| `ExecutionReceipt` | Status, actor, result, error and idempotency key. |
| `DeliveryReceipt` | Decision, channel, status and detail. |

## The boundary

The app kit is optional. A host that only needs the answer calls `decide` or `Layer`. A host that
also executes, records, streams or delivers adds the rest.

The app kit defines the ports. The host implements them:

- where state and checkpoints are saved;
- how stream state is resumed;
- how skills, events and approvals are reached;
- where a decision is delivered;
- how long records, traces and outcomes are kept.

The host also owns credentials, transport, execution handlers, retries and channel fallback. LAIX
does not open a database, call a model provider or deliver a message on its own.

## Reading map

Read in order. Each section opens with a short index that lists its pages in reading order.

| Section | Covers |
|---|---|
| [Build](01-build/README.md) | The adapter, one decision and policy selection. |
| [Run](02-run/README.md) | The runtime loop, streams and perception. |
| [Execute](03-execute/README.md) | Execution, recovery, proposals and records. |
| [Connect](04-connect/README.md) | Stores, platform and delivery. |
| [Operate](05-operate/README.md) | Bench, metrics and deployment. |

## Where the code lives

| Path | Contents |
|---|---|
| `appkit/layer.py` | `Layer`, the one-decision surface. |
| `appkit/runtime/` | decision runtime, execution, saga, state and stores. |
| `appkit/streaming/` | session, window, sources, checkpoint and timeline. |
| `appkit/live_context/` | the host-driven detector loop. |
| `appkit/audit/` | decision record, proposal, approval, undo and audit events. |
| `appkit/delivery/` | delivery port, receipt and the null implementation. |
| `appkit/platform/` | platform, in-memory platform, skill call, approvals and events. |
| `appkit/bench/` | case, suite, row, report, runner and planner bench. |

The core map is [Core overview](../02-core/README.md). The vocabulary is in the
[glossary](../04-concepts/glossary.md).
