# PPMA + LAIX: task decisions below the activation core

PPMA and LAIX meet at one seam:

> PPMA decides what a trigger becomes. LAIX decides what one bounded task does next.

JEV is a judgment engine inside that task; LAIX is the layer around it.

## 1. The boundary

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Owner | PPMA Epistemic Core | LAIX |
| Question | What does this trigger become for PPMA? | What is the next move for this task? |
| Output | `NOOP` · `UPDATE_STATE` · `ISSUE_COMMAND` · `DISPATCH` | `wait` · `observe` · `guide` · `ask` · `act` · `verify` · `escalate` |
| Scope | PPMA's next cycle | One bounded task |
| Creates work | Yes: commands, dispatches, plans, filters | No |
| Commits | PPMA's commit path | No |
| Executes | PPMA, or the app through its execution policy | No |

PPMA keeps:

- memory, ingestion, connectors and proactivity;
- permissions, missions and app execution policy;
- Commander and activation decisions;
- calibration, provenance, commit and execution;
- the user interface.

LAIX supplies:

- the task verb and reason code;
- confidence, score and breakdown;
- evidence, alternatives and constraints applied;
- action id and intent;
- `requires_approval`, `reversible` and `undo_hint`;
- a task decision id.

One line:

```text
PPMA decides what the trigger becomes.
LAIX decides what the task does next.
```

## 2. JEV vs LAIX: not a choice

JEV is a decision model:

```text
state + question + allowed answers
              ↓
choice / score / probabilities / confidence
```

LAIX is a decision layer:

```text
situation + options + constraints
              ↓
one task decision: verb + reason + approval + action
```

Keep JEV. Put it inside a LAIX policy where judgment is needed.

```text
JEV                     → judgment
LAIX                    → task decision: constraints, approval, escalation, verification
PPMA                    → activation, calibration, commit, execution, record
```

If PPMA only needs one closed judgment, JEV is enough. LAIX is for a reusable task-decision layer across many bounded decisions: JEV gives the judgment; LAIX gives the task-decision contract that uses it.

## 3. Why PPMA needs it

PPMA has activation policy in the Commander and execution policy in the apps. The gap is one generic task-decision policy contract shared by the Commander, missions and apps.

LAIX gives PPMA:

- **Policy composition.** JEV, an LLM or deterministic rules can sit inside one policy.
- **Decision semantics.** Constraints, approval, escalation and verification travel with the decision.
- **One contract.** Attention, action, allocation, negotiation, verification and escalation use the same decision shape.
- **Model independence.** Swap JEV or the LLM behind the same contract.
- **Testability.** Bounded policies can be replayed, compared and benchmarked.
- **Fewer model calls.** Decisions that do not need a full Commander prompt can run as a policy.

## 4. Integration

LAIX is a tool or task policy below the activation core, called inside PPMA's existing path.

```text
PPMA trigger
  → Commander / ActivationDecision
  → bounded task
  → LAIX task policy
       ├── JEV judgment when needed
       ├── constraints / approval / escalation / verification
       └── Decision
  → PPMA calibrates, records, commits, executes
```

Deployment:

- a separate `ppma-laix` package or service;
- imports `laix` core and `ppma-contracts`;
- exposes `laix.decide` as an `effect: none` query tool or a mission tool;
- one `DecisionRequest` in, one `Decision` out; PPMA keeps memory, calibration, provenance, commit and execution.

The request carries the bounded task. The decision carries the task verb, reason, confidence, action, approval and decision id. See [boundaries](boundaries.md) for the full seam.

## 5. The boundary in practice

- PPMA's `handle` remains the single reasoning path.
- JEV and LLM calls stay with PPMA's engines or the policy adapter.
- PPMA keeps memory, calibration, provenance, commit and execution.
- PPMA accepts, modifies or rejects the task decision, and records the LAIX id as a reference.

This preserves PPMA's one reasoning path, one commit path and one `ask` boundary.

## 6. First proof

Pick one bounded decision class:

- a mission step; or
- a Commander subtask that currently needs a full LLM ask.

Implement it as a LAIX policy with JEV as the judgment step. Expose it as an `effect: none` tool or a mission tool. Compare:

- model calls and tokens;
- latency;
- determinism and replay;
- decision quality;
- audit clarity.

Expand only if it wins. If it does not, keep JEV and the current path.

## 7. One-slide version

```text
PPMA + LAIX — task decisions below the activation core

PPMA keeps                          JEV → LAIX
- memory, Commander/activation      - JEV: judgment
- calibration, commit, provenance   - LAIX: one task decision
- execution, missions, apps         - keep JEV inside LAIX

LAIX adds                           Boundary
- policy composition                 - LAIX is a tool/policy below the Commander
- constraints, approval,             - one reasoning path: PPMA's Commander
  escalation, verification           - PPMA keeps authority
- one contract across tasks          - PPMA calibrates, records, commits
- model independence, replay

First proof: one bounded decision class → measure calls, latency, determinism, quality.
```
