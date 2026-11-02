# Boundaries: LAIX and the host

LAIX produces a decision for one bounded task. A host owns the product around it.

The boundary assigns the activation decision to PPMA and the task decision to LAIX. PPMA owns the activation core, the commit path and the execution lifecycle. LAIX provides the task decision. The same boundary applies to any host; PPMA is the primary case because it already has its own decision vocabulary and lifecycle.

- PPMA owns the activation decision, commit, execution and records.
- LAIX owns the task decision inside one bounded task.
- PPMA uses LAIX core only, as a task policy layer below its activation core.

## 1. The PPMA–LAIX boundary

PPMA owns the activation decision. LAIX owns the task decision.

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Owner | PPMA's Epistemic Core | LAIX core |
| Input | A host trigger: event, timer, answer, outcome or surface change | A bounded task: subject, situation, options and constraints |
| Question | What does this trigger become for PPMA? | What is the next move for this task? |
| Output | `NOOP` · `UPDATE_STATE` · `ISSUE_COMMAND` · `DISPATCH` | `wait` · `observe` · `guide` · `ask` · `act` · `verify` · `escalate` |
| Scope | PPMA's next cycle | One task |
| Lifecycle | PPMA creates, continues and closes the work | PPMA owns the lifecycle; LAIX returns the decision |
| Effect | Starts or changes work | Chooses the next move inside the work |

PPMA's activation core is its Epistemic Core: the Ingestor and the Commander. The Ingestor decides what enters memory; the Commander decides what PPMA does next. Both commit through PPMA's commit path.

In one line:

```text
PPMA decides what the trigger becomes.
LAIX decides what one bounded task does next.
```

```text
PPMA trigger
  ▼
PPMA Epistemic Core / Commander
  │ activation decision: NOOP | UPDATE_STATE | ISSUE_COMMAND | DISPATCH
  │
  ├── no bounded task ──────────────────────────────► PPMA output
  │
  └── bounded task
        │  builds a DecisionRequest
        ▼
      laix decide()
        │  returns a task Decision
        ▼
      PPMA
        │  accepts, modifies or rejects the task decision
        │  calibrates, records, commits, executes
        ▼
      PPMA output
```

PPMA keeps:

- memory and history;
- ingestion, filters, triggers and routing;
- connectors, credentials and transports;
- proactivity, permissions, clearances and owner settings;
- missions, workers, lifecycle and budgets;
- app and tool choice;
- app execution policy;
- command confidence and calibration;
- decision records, outcomes and provenance;
- commit and execution;
- the user interface.

LAIX supplies:

- the task verb and reason code;
- the rationale and confidence;
- the score and breakdown;
- the action id and intent;
- `requires_approval`, `reversible` and `undo_hint`;
- the task decision id and trace id.

The activation vocabulary belongs to PPMA. LAIX returns a task decision; PPMA owns the command, execution and record that follow.

## 2. The two integration shapes

Both shapes are first-class. The choice belongs to the host.

### 2.1 PPMA with its own activation core

PPMA decides what the trigger becomes. When the work is a bounded task, PPMA asks LAIX for the task decision.

```text
PPMA activation core
  │  decides: NOOP | UPDATE_STATE | ISSUE_COMMAND | DISPATCH
  ├── no bounded task ────────────────────────► PPMA output
  └── bounded task
        │  DecisionRequest
        ▼
      LAIX
        │  Decision
        ▼
      PPMA activation core
        │  accept | modify | reject
        │  calibrate, record, commit, execute
        ▼
      PPMA output
```

The activation core owns PPMA's reasoning path and final decision. LAIX operates as a task policy layer below it. LAIX can be exposed to the Commander as a query tool (`effect: none`) or to a mission as a tool; the Commander's `ask` or the mission agent calls it within the existing path. PPMA treats the result as one input: it accepts, modifies or rejects it.

The clean deployment is a separate `ppma-laix` tool or service:

- it imports only `laix` core and `ppma-contracts`;
- it exposes `laix.decide` as a query tool (`effect: none`) or a mission tool;
- it receives a `DecisionRequest` and returns a `Decision`.

The service is stateless: a request in, a decision out. PPMA owns memory, commit and execution.

### 2.2 LAIX supplies the task decision

A host without its own activation core asks LAIX directly and acts on the answer.

```text
host
  │  builds a DecisionRequest for one bounded task
  ▼
laix decide()
  │  returns a Decision
  ▼
host
  │  acts
  │  records the outcome
  ▼
host state
```

`decide` is stateless between calls. The outcome belongs to the host: the host records it, and its next request can carry what it learned. When the host uses LAIX's outcome learning, it passes the outcome to that learner explicitly; `decide` itself does not receive it.

The host owns execution, records and delivery. The next request carries the result.

## 3. The seam

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

PPMA keeps the domain nouns in how it builds the request and reads the decision. LAIX sees only the generic fields above.

## 4. Ids, confidence, provenance and commit

Each decision keeps the id of the system that made it. A LAIX task decision carries LAIX's `decision_id`; a PPMA activation decision or command carries PPMA's id. PPMA's provenance record holds the request, the LAIX decision id and how PPMA used the decision.

LAIX returns a confidence for its task decision. PPMA treats it as one source estimate and emits its own calibrated confidence to apps.

PPMA commits its own state. The LAIX decision is recorded and applied within that commit.

## 5. The optional app kit

Above `laix` there is `laix.appkit`, the optional package for hosts that want the integration surface around a decision: `Layer`, the runtime, execution, records, delivery and platform.

`laix.appkit` depends on `laix`. A host uses the core alone or adds the app kit. The app kit provides the runtime around a core decision.

PPMA uses the core alone: it already has execution, records and commit, so it calls `laix` directly:

```python
from laix import decide

decision = decide(request)[0]
```

A host that wants the app kit's runtime calls `Layer`:

```python
from laix import Layer

layer = Layer()
decision = layer.decide(request)[0]
```

The app kit is a separate surface. Packaging may ship the two together or separately; the boundary is the same.

## 6. Rules

1. A decision is bounded to one task. The host defines the task.
2. LAIX chooses the task's next move. The host owns activation, commit, execution and persistence.
3. A host with its own activation core uses LAIX as a task policy layer below that core.
4. The host core owns the reasoning path and the decision authority for activation, commit and execution.
5. LAIX confidence is an input to the host's calibration.
6. Each owner keeps its own decision ids. The host records a LAIX decision id as a reference, not as its own.
7. Execution and records follow task ownership: the host, or the app kit when the host chooses it.
8. Memory, connectors, permissions, proactivity, missions and app policy stay in the host.
9. Core imports only the standard library and its own modules. App kit imports the standard library, core and its own modules. The host imports LAIX.
10. A host that already has execution, records and commit uses the core only.
