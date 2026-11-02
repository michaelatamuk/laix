# Boundaries: core, app kit and host

LAIX has three layers:

| Layer | What it is |
|---|---|
| **LAIX core** | contracts, decision shape, policies, engines, outcomes and evaluation |
| **LAIX app kit** | optional integration: Layer, execution, records, delivery, platform, state and live context |
| **Host** | the product that uses LAIX: memory, ingestion, connectors, orchestration, permissions and user settings |

The rule is simple:

> The host imports LAIX. LAIX uses its own modules and generic vocabulary.

## The two LAIX surfaces

### `laix.core`

Use this from a mission, agent or service that needs a decision.

```python
from laix import DecisionRequest, decide

decision = decide(request)[0]
```

or, from the core package directly:

```python
from laix.core import DecisionRequest, decide
```

It contains:

- the `decide()` entry point and request selection;
- contracts;
- request and decision shapes;
- attention and the policy packs;
- resource admission;
- sensing contracts;
- the UCB learner and outcome ledger;
- the parity harness.

Core imports contracts, policies and evaluation. Layer, execution, records, delivery, platform and the live-context loop live in the app kit.

### `laix.appkit`

Use this when an app wants the optional app-facing parts.

```python
from laix.appkit import Layer, ExecutionBridge
```

It contains:

- `Layer`, which uses core selection and adds the runtime, execution and decisions;
- execution and runtime;
- decision records and proposals;
- delivery;
- platform;
- the live-context loop;
- bench.

The app kit is optional and frozen. Core is the decision layer; the app kit connects it to an app.

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

These are product concerns. Each host defines them.

## What belongs to LAIX

LAIX owns:

| Area | LAIX owns |
|---|---|
| Decision shape | verb, reason, confidence, action and approval |
| Task policies | attention/action packs, allocation, replanning, negotiation, safety, verification, escalation |
| Decision engines | utility, planning and learned policies |
| Task lifecycle | execute, cancel, undo, receipt |
| Task outcomes | measured outcome and learning |
| Evaluation | policy comparison and parity |

LAIX sees the request and its options. The host keeps the task and its reason.

## The seam

```text
host
  │  builds a DecisionRequest for a bounded task
  ▼
laix.core decide()
  │  returns a Decision
  ▼
host
  │  acts, then reports the outcome
  ▼
laix.core
```

The host may use `laix.appkit` for execution and records. The host drives that integration.

## Rules

1. Core imports only core modules.
2. The app kit imports core and its own modules.
3. Host concerns stay in the host.
4. Adapters live in the host and call LAIX.
5. A decision is bounded to one task. The host decides when a task exists.
6. Add app-kit features when a host uses them.
