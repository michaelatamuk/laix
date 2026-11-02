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
      laix.core decide()
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
- app execution policy;
- command confidence and calibration;
- provenance, commit and execution;
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
laix.core decide()
  │  returns a Decision
  ▼
host
  │  acts, then reports the outcome
  ▼
laix.core
```

The host may use `laix.appkit` for execution, records and delivery, or keep those in the host.

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

PPMA keeps the domain nouns. LAIX keeps the generic vocabulary.

| Concern | Owner |
|---|---|
| Whether a task exists | PPMA |
| The task's goal, options and constraints | PPMA |
| The next move inside the task | LAIX |
| Activation: notice, remember, interrupt, act, dispatch | PPMA |
| Which app or tool is called | PPMA |
| Task lifecycle | PPMA |
| Execution | PPMA, or the app through its execution policy |
| Decision record, outcome and provenance | PPMA |
| Memory, connectors, permissions, proactivity | PPMA |
| Calibration of emitted confidence | PPMA |
| Generic decision schema and task policies | LAIX |
| Decision ids | Each owner, in its own namespace |

## 4. Ids, confidence, provenance and commit

**Ids.** LAIX's `decision_id` identifies the LAIX task decision. PPMA's decision id identifies PPMA's activation decision or command. They are different namespaces. PPMA records the LAIX id as an external reference when it uses the decision.

**Confidence.** LAIX returns a confidence for its task decision. PPMA calibrates the confidence it emits to apps. LAIX's value is a source estimate; PPMA's calibrated claim is the one PPMA emits.

**Provenance.** PPMA records the request, the LAIX decision id and whether it used, modified or rejected the decision. LAIX returns the decision shape and keeps no PPMA record.

**Commit.** PPMA commits its own state through its own path. LAIX returns a decision; PPMA records and applies it. The app kit stays outside PPMA's commit path.

## 5. Roles

| Role | What it owns |
|---|---|
| **LAIX core** (`laix.core`) | The decision contract, the task policies and the engines that produce a task decision. Deterministic, standard-library only; host state stays with the host. |
| **LAIX app kit** (`laix.appkit`) | The optional integration around a core decision: `Layer`, runtime, execution, records, delivery and platform. |
| **Host** | The product: memory, ingestion, connectors, orchestration, proactivity, permissions, missions, app policy, calibration, commit, execution and UI. |

The dependency direction is fixed:

```text
host
 ├── laix.core
 └── laix.appkit
        └── laix.core
```

Core imports only the standard library and its own modules. App kit imports the standard library, `laix.core` and its own modules. The host imports LAIX. Dependencies point from the host to LAIX.

## 6. Core and app kit are separate surfaces

A host chooses its surface.

**Core only.**

```python
from laix import decide

decision = decide(request)[0]
```

The host brings its own execution, records, delivery and persistence. This is the surface for PPMA: PPMA already has execution, records and commit, so it uses the core only.

**Core plus app kit.**

```python
from laix import Layer

layer = Layer()
decision = layer.decide(request)[0]
```

`Layer` uses core selection and adds the runtime: ids, traces, state, execution, records and delivery. The host still owns its memory, connectors, permissions and app policy.

The app kit is optional. The core is the stable integration surface. Packaging may ship them together or separately; the boundary is the same.

## 7. Rules

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
