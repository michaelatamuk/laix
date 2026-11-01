# Boundaries: core, app kit and host

LAIX has three layers:

| Layer | What it is |
|---|---|
| **LAIX core** | contracts, decision shape, policies, engines, outcomes and bench |
| **LAIX app kit** | optional integration: attention, execution, records, delivery, platform, state and live context |
| **Host** | the product that uses LAIX: memory, ingestion, connectors, orchestration, permissions and user settings |

The rule is simple:

> The host imports LAIX. LAIX never imports or names the host.

## The two LAIX surfaces

### `laix.core`

Use this from a mission, agent or service that needs a decision.

```python
from laix.core import DecisionRequest, PolicyDecision, PolicyRegistry
```

It contains:

- contracts;
- request and decision shapes;
- policies and the policy registry;
- the UCB learner and outcome ledger;
- the parity harness.

It does not load attention, execution, records, delivery or platform.

### `laix.appkit`

Use this when an app wants the optional app-facing parts.

```python
from laix.appkit import Layer, Signal, Context, ExecutionBridge
```

It contains:

- `Layer` and the built-in request routing;
- attention;
- execution and runtime;
- decision records and proposals;
- delivery;
- platform;
- live context;
- bench.

The app kit is optional and frozen. It is useful, but it is not the decision core.

The TypeScript package uses the same folders under `src/core` and `src/appkit`; it exports one
entry point, `laix`.

## What belongs to the host

The host owns:

| Area | Host owns |
|---|---|
| Memory | persistent entries, surfaces, history |
| Ingestion | events, filters, triggers, routing |
| Connectors | apps, credentials, transports |
| Orchestration | whether to notice, remember, interrupt or dispatch |
| Proactivity | when the product may take the user's attention |
| Permissions | scopes, clearances, holders, owner settings |
| Missions | dispatch, workers, lifecycle, budgets |
| App policy | auto-execute vs ask per app and tool |
| Command confidence | calibration of the host's own commands |

These are product concerns. They vary by host and cannot be generic LAIX contracts.

## What belongs to LAIX

LAIX owns:

| Area | LAIX owns |
|---|---|
| Decision shape | verb, reason, confidence, action and approval |
| Task policies | attention/action packs, allocation, replanning, negotiation, safety, verification, escalation |
| Decision engines | utility, planning and learned policies |
| Task lifecycle | execute, cancel, undo, receipt |
| Task outcomes | measured outcome and learning |
| Evaluation | policy comparison, parity and bench |

LAIX does not know why the host asked. It only knows the request and the options.

## The seam

```text
host
  │  builds a DecisionRequest for a bounded task
  ▼
laix.core
  │  returns a Decision
  ▼
host
  │  acts, then reports the outcome
  ▼
laix.core
```

The host may use `laix.appkit` for attention, execution and records. That is still host-driven integration, not a second orchestrator.

## Rules

1. LAIX core does not import the app kit.
2. The app kit does not import a host.
3. LAIX never adds host memory, ingestion, connectors, permissions, proactivity or missions.
4. The host may add a LAIX adapter; LAIX never adds a host adapter.
5. A decision is bounded to one task. The host decides when a task exists.
6. New app-kit features need a host that uses them. No speculative expansion.
