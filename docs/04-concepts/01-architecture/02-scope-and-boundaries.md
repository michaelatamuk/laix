# Scope and boundaries

LAIX produces a decision for one bounded task. A host owns the product around it.

The boundary assigns the **task decision** to LAIX and the **activation decision** to the layer above
it. PPMA is the primary case because it already has its own decision vocabulary and lifecycle, but the
same boundary applies to any host.

## The three layers

| Layer | Owns | Does not own |
|---|---|---|
| **LAIX core** | The request and decision contract, policies, planners, signal attention, commitments, learning primitives and evaluation primitives. | Storage, UI, execution, delivery, credentials. |
| **LAIX app kit** | The optional runtime: `Layer`, decision runtime, streaming, execution bridge, records, stores, platform and delivery ports. | The database, transport, credentials and the host's domain rules. |
| **Host** | The product, data, UI, execution, storage, delivery, permissions, retention and the domain nouns. | The decision contract and the decision semantics. |

The core is stateless. The app kit adds state and execution surfaces. The host decides which of the
two it uses.

## The seam

One request crosses the boundary. An action request returns one decision; an attention request
returns one decision per signal.

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

The host keeps the domain nouns in how it builds the request and reads the decision. LAIX sees the
generic fields above. The full shape is in
[the decision contract](../../02-core/01-contract/01-decision-contract.md).

## The two integration shapes

Both shapes are first-class. The choice belongs to the host.

### Core only

The host already has execution, records and commit. It calls `decide` and acts on the answer.

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

`decide` is stateless between calls. The outcome belongs to the host: the host records it, and its
next request can carry what it learned.

### Core plus app kit

The host wants the runtime around the decision: a single `Layer`, execution, records, stores,
streaming and delivery.

```python
from laix import Layer

layer = Layer()
decision = layer.decide(request)[0]
```

The app kit defines the ports; the host implements them. See
[App-kit overview](../../03-appkit/README.md).

## The PPMA boundary

PPMA owns the activation decision. LAIX owns the task decision.

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Owner | PPMA's Epistemic Core | LAIX core |
| Input | A host input: event, timer, answer, outcome or surface change | A bounded task: subject, situation, options and constraints |
| Question | What is the system's next move? | What is the task's next move? |
| Output | `NOOP`, `UPDATE_STATE`, `ISSUE_COMMAND` or `DISPATCH` | `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate` |
| Scope | Across the system | Inside one task |
| Lifecycle | PPMA creates, continues and closes the work | PPMA owns the lifecycle; LAIX returns the decision |
| Effect | Starts or changes work | Chooses the next move inside the work |

In one line:

```text
PPMA decides what the system does next.
LAIX decides what one task does next.
```

The activation vocabulary belongs to PPMA. LAIX returns a task decision; PPMA owns the command,
execution and record that follow. The detailed call shape, the four activation paths and the JEV
example are in [PPMA integration](../02-positioning/02-ppma-integration.md).

## Ids, confidence, provenance and commit

Each decision keeps the id of the system that made it. A LAIX task decision carries LAIX's
`decision_id`; a PPMA activation decision or command carries PPMA's id. PPMA's provenance record holds
the request, the LAIX decision id and how PPMA used the decision.

LAIX returns a confidence for its task decision. PPMA treats it as one source estimate and emits its
own calibrated confidence to apps.

PPMA commits its own state. The LAIX decision is recorded and applied within that commit.

## Rules

1. A decision is bounded to one task. The host defines the task.
2. LAIX chooses the task's next move. The host owns activation, commit, execution and persistence.
3. A host with its own activation core uses LAIX as a task policy layer below that core.
4. The host core owns the reasoning path and the decision authority for activation, commit and
   execution.
5. LAIX confidence is an input to the host's calibration.
6. Each owner keeps its own decision ids. The host records a LAIX decision id as a reference.
7. Execution and records follow task ownership: the host, or the app kit when the host chooses it.
8. Memory, connectors, permissions, proactivity, missions and app policy stay in the host.
9. Core imports the standard library and its own modules. App kit imports the standard library, core
   and its own modules. The host imports LAIX.
10. A host that already has execution, records and commit uses the core.

## Related

- [System architecture](01-system-architecture.md) - the decision and the parts.
- [PPMA integration](../02-positioning/02-ppma-integration.md) - the activation layer in detail.
- [App-kit overview](../../03-appkit/README.md) - the optional runtime.
- [Execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md) - the write boundary.
- [Glossary](../04-reference/01-glossary.md) - the vocabulary.
