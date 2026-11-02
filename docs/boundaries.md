# Boundaries: core, app kit and host

LAIX is a decision layer with two surfaces and one host-facing seam.

| Role | What it is | Package |
|---|---|---|
| **Core** | The decision contract and the task policies that produce a decision. | `laix.core` |
| **App kit** | Optional integration: a facade, runtime, execution, records, delivery and platform. | `laix.appkit` |
| **Host** | The product that owns the task, the state, the people and the apps. | the host |

The dependency direction is fixed:

```text
host
 ├── laix.core
 └── laix.appkit
        └── laix.core
```

Core imports only the standard library and its own modules. App kit imports the standard library, `laix.core` and its own modules. The host imports LAIX. LAIX never imports the host.

## 1. What each role owns

### Core

Core owns the decision itself:

- the request and decision shapes;
- the verbs and reason codes;
- task policies: attention, action, active perception, safety, replanning, allocation, negotiation, preference elicitation, verification, escalation and bandit;
- the routing between a policy, the action engine and the attention engine;
- outcome learning and evaluation;
- sensing contracts, resource admission and schema.

Core is deterministic and uses only the standard library. It holds no host state. It receives a `DecisionRequest` and returns a `Decision`, or one decision per signal.

### App kit

App kit owns the optional integration around the decision:

- `Layer`, the app-facing facade over core selection;
- the runtime: ids, traces, state and stored decisions;
- execution, approval, cancel, undo and receipts;
- decision records, proposals and audit;
- delivery ports and receipts;
- the platform contract;
- the live-context loop;
- the bench.

App kit is not the decision authority. It provides the runtime and records for the decisions a host chooses to run.

### Host

The host owns the product. It can be a single app, an agent, a service or a proactive system. It owns:

- memory and history;
- ingestion, filters, triggers and routing;
- connectors, credentials and transports;
- orchestration: whether to notice, remember, interrupt, act or dispatch;
- proactivity: when the product may take the user's attention;
- permissions, clearances, approvals and owner settings;
- missions, workers, lifecycle and budgets;
- app policy: auto-execute versus ask, per app and tool;
- command confidence and calibration;
- the user interface;
- persistence of the host's own state.

The host defines the task. It decides when a task exists, what its goal is, which options are available, and what happens after the decision.

## 2. Two decision scopes

LAIX decisions are **task decisions**. A host may also have **activation decisions**. These are different scopes, not different ranks. The host component that owns activation decisions is the host's **activation core**.

| | Task decision | Activation decision |
|---|---|---|
| Owner | LAIX | Host |
| Unit | One bounded task | One trigger or one host cycle |
| Question | What should this task do next? | What should the host do with this trigger? |
| Output | `wait`, `observe`, `guide`, `ask`, `act`, `verify`, `escalate` | Host-defined; may create, continue or stop work |
| Creates a task | No | Yes |
| Commits host state | No | The host core |
| Executes an action | No | The host, or app kit when the host uses it |
| Records the lifecycle | No | The host, or app kit when the host uses it |
| Example | "Close the valve", "ask for the missing date", "escalate this case" | "Ignore this event", "update memory", "issue a command", "dispatch a mission" |

An activation decision can create the task in which a task decision runs. A task decision never creates the next task.

The distinction is scope and authority, not importance. A host with an activation core keeps it; LAIX operates inside the tasks that core creates.

## 3. Two integration shapes

Both shapes are first-class. The choice is a property of the host, not a version of LAIX.

### 3.1 LAIX supplies the task decision

The host builds a request, calls LAIX, and acts on the decision.

```text
host
  │  builds a DecisionRequest for one bounded task
  ▼
laix.core decide()
  │  returns a Decision
  ▼
host
  │  acts, then reports the outcome
  ▼
laix.core
```

This is the default shape. The host may use `laix.appkit` for execution, records and delivery, or keep those in the host.

### 3.2 The host has its own activation core

The host core decides what the trigger becomes. When the work is a bounded task, the host core asks LAIX for the task decision.

```text
host trigger
  ▼
host activation core
  │  decides: noop, update state, issue a command, dispatch a task
  ├── no task ───────────────────────────────► host output
  └── bounded task
        │  builds a DecisionRequest
        ▼
      laix.core decide()
        │  returns a task Decision
        ▼
      host activation core
        │  accepts, modifies or rejects the task decision
        │  commits, records, executes
        ▼
      host output
```

The host core remains the sole reasoning path and the sole authority for activation, commit and execution. LAIX operates as a task policy layer below it. The host core treats LAIX's decision as one input: it accepts, modifies or rejects it.

This shape applies to a host that already has its own decision vocabulary and lifecycle, such as a proactive project agent with activation decisions like `NOOP`, `UPDATE_STATE`, `ISSUE_COMMAND` and `DISPATCH`. Those decisions stay in the host. LAIX answers the task-level question the host core asks.

### A worked example

A proactive host receives an email that mentions a deadline.

```text
1. Host activation core: UPDATE_STATE
   The thread enters memory. No task yet.

2. Host activation core: ISSUE_COMMAND / DISPATCH
   The host creates a bounded task: "handle the deadline in this thread".

3. LAIX task decision: ask
   The email gives two possible dates, so the task needs the user's choice.

4. Host: ui.ask
   The question reaches the user. The answer returns as an event.

5. LAIX task decision: act
   The date is known. The host creates the calendar block.

6. Host activation core: UPDATE_STATE
   The outcome enters memory. The task closes.
```

The activation decisions are the host's. The task decisions are LAIX's. The host chooses when the task exists, what it contains and what happens after each answer.

## 4. The seam

One request crosses the boundary. An action request returns one decision; an attention request returns one decision per signal.

```python
from laix import decide

decision = decide(request)[0]
```

The request carries:

- the subject and the moment;
- a situation and options, or signals and a context;
- goals, beliefs, observations and constraints;
- attributes, confidence and confidence source.

The decision carries:

- `verb`, `reason_code`, `rationale`;
- `confidence`, `score`, `breakdown`;
- `action_id`, `intent`, `requires_approval`, `reversible`, `undo_hint`;
- `decision_id`, `trace_id`, `policy_version`, `created_at`.

The host keeps the domain nouns. LAIX keeps the generic vocabulary.

| Concern | Owner |
|---|---|
| Whether a task exists | Host |
| The task's goal, options and constraints | Host |
| The next move inside the task | LAIX |
| Activation: notice, remember, interrupt, act, dispatch | Host |
| Which app or tool is called | Host |
| Execution | Host, or app kit when the host chooses it |
| Decision record and execution history | Host, or app kit when the host chooses it |
| Task lifecycle | Host |
| Memory, connectors, permissions, proactivity | Host |
| Calibration of emitted confidence | Host |
| Generic decision schema and task policies | LAIX |
| Decision ids | Each owner, in its own namespace |

## 5. Ids, confidence, provenance and commit

These are separate on purpose.

**Ids.** LAIX's `decision_id` identifies the LAIX decision. The host's decision id identifies the host's activation decision or command. They are different namespaces. The host records the LAIX id as an external reference when it uses the decision.

**Confidence.** LAIX returns a confidence for its decision. When the host emits a calibrated confidence to an app, the host calibrates it. LAIX's value is a source estimate, not the host's calibrated claim.

**Provenance.** The host records the request, the LAIX decision id and whether it used, modified or rejected the decision. LAIX returns the decision shape and keeps no host record.

**Commit.** LAIX does not commit host state. The host commits through its own path. App kit keeps its own runtime records and does not write host state.

## 6. Core and app kit are separate surfaces

A host chooses its surface.

**Core only.**

```python
from laix import decide

decision = decide(request)[0]
```

The host brings its own execution, records, delivery and persistence. `laix.appkit` is never imported. A host obtains a decision without the app kit.

**Core plus app kit.**

```python
from laix import Layer

layer = Layer()
decision = layer.decide(request)[0]
```

`Layer` uses core selection and adds the runtime: ids, traces, state, execution, records and delivery. The host still owns its own memory, connectors, permissions and app policy.

The app kit is optional. The core is the stable integration surface. Packaging may ship them together or separately; the boundary is the same.

## 7. Rules

1. A decision is bounded to one task. The host defines the task.
2. LAIX chooses the task's next move. The host owns activation, commit, execution and persistence.
3. The host maps its domain into generic request fields. LAIX returns generic vocabulary.
4. Core imports only the standard library and its own modules. App kit imports the standard library, core and its own modules. The host imports LAIX.
5. A host with its own activation core uses LAIX as a task policy below that core.
6. The host core remains the sole reasoning path and the sole decision authority for activation, commit and execution.
7. Each owner keeps its own decision ids. The host records a LAIX decision id as a reference, not as its own.
8. LAIX confidence is an input to the host's calibration.
9. Execution and records follow task ownership: app kit when the host chooses it, otherwise the host.
10. Memory, connectors, permissions, proactivity, missions and app policy stay in the host.
