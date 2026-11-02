# PPMA + LAIX: from judgment to task decision to action

PPMA is an activation system. LAIX is a task-decision layer. JEV is a judgment engine. Together they form one path:

```text
judgment → task decision → action
```

## 1. Three roles

| Role | Product | Contribution |
|---|---|---|
| **Judgment** | JEV | The answer to one closed question, with probabilities and confidence. |
| **Task decision** | LAIX | Constraints, approval, escalation, verification and one decision shape for a bounded task. |
| **Activation** | PPMA | What the trigger becomes, memory, calibration, commit, execution and the user interface. |

A trigger becomes work in PPMA. The work becomes a bounded task. LAIX decides the task's next move. PPMA acts.

## 2. Two decision scopes

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Question | What does this trigger become? | What is the next move for this task? |
| Output | `NOOP` · `UPDATE_STATE` · `ISSUE_COMMAND` · `DISPATCH` | `wait` · `observe` · `guide` · `ask` · `act` · `verify` · `escalate` |
| Scope | PPMA's next cycle | One bounded task |
| Work | Commands, dispatches, plans, filters | The task's next move |
| Lifecycle | PPMA owns it | LAIX returns the decision |

PPMA runs the system. LAIX answers the task question.

## 3. JEV inside LAIX

JEV produces a judgment:

```text
state + question + allowed answers
              ↓
choice / score / probabilities / confidence
```

LAIX produces a task decision:

```text
situation + options + constraints
              ↓
one task decision: verb + reason + approval + action
```

JEV is the chooser inside a LAIX policy. JEV remains PPMA's judgment engine; the LAIX policy composes its answer with constraints, approval, escalation, verification and the decision record.

JEV alone is the right tool for one closed judgment. LAIX is the right layer when PPMA needs a shared task-decision contract across many bounded decisions.

## 4. What PPMA gains

- **One task-decision contract** across the Commander, missions and apps.
- **Policy composition:** JEV, an LLM or deterministic rules inside one policy.
- **Decision semantics:** constraints, approval, escalation and verification travel with the decision.
- **Model independence:** swap JEV or the LLM behind the same contract.
- **Replay and comparison:** bounded policies can be tested, replayed and benchmarked.
- **Fewer model calls:** decisions that do not need a full Commander prompt run as a policy.

## 5. How they meet

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

PPMA calls LAIX as a tool or task policy inside the Commander or a mission. The call rides PPMA's existing path; calibration, commit and execution stay with PPMA. LAIX returns a `Decision`. PPMA calibrates the confidence it emits, records the decision, commits the outcome and executes.

Deployment:

- a separate `ppma-laix` package or service;
- imports `laix` core and `ppma-contracts`;
- exposes `laix.decide` as an `effect: none` query tool or a mission tool;
- one `DecisionRequest` in, one `Decision` out.

## 6. The interface

| PPMA supplies | LAIX returns |
|---|---|
| Subject and moment | Verb and reason code |
| Situation and options, or signals and context | Confidence, score and breakdown |
| Goals, beliefs and constraints | Evidence, alternatives and constraints applied |
| Attributes and confidence source | Action id, intent, approval and reversibility |

PPMA supplies the task. LAIX returns the decision. PPMA acts on it.

PPMA records the LAIX decision id as a reference and calibrates the confidence it emits. LAIX confidence is a source estimate.

## 7. First proof

Start with one bounded decision class:

- a mission step; or
- a Commander subtask that currently needs a full LLM ask.

Implement it as a LAIX policy with JEV as the judgment step. Expose it as an `effect: none` tool or a mission tool.

Measure:

- model calls and tokens;
- latency;
- determinism and replay;
- decision quality;
- audit clarity.

Use the result to choose the next decision class.

## 8. One-slide version

```text
PPMA + LAIX — from judgment to task decision to action

JEV            → judgment: one closed question
LAIX           → task decision: constraints, approval, escalation, verification
PPMA           → activation, memory, calibration, commit, execution

PPMA owns the trigger and the lifecycle.
LAIX owns the task decision.
PPMA calls LAIX inside the Commander or a mission.

Why LAIX:
- one task-decision contract across Commander, missions and apps
- JEV, LLM and deterministic rules compose in one policy
- model independence, replay and comparison
- fewer model calls for bounded decisions

Start: one bounded decision class. Measure calls, latency, determinism, quality.
```
