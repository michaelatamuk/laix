# PPMA + LAIX: the task-decision layer

PPMA decides what a trigger becomes. LAIX decides what one bounded task does next. JEV is a judgment engine that can sit inside a LAIX policy.

## 1. Why LAIX

PPMA needs a task decision, not only a judgment. LAIX supplies:

- **A decision, not a score.** It returns a verb, a reason, a confidence, an action and an approval flag.
- **Policy composition.** JEV, an LLM or deterministic rules can sit inside one policy.
- **Decision semantics.** Constraints, approval, escalation and verification travel with the decision.
- **One contract.** Attention, action, allocation, negotiation, verification and escalation use the same decision shape.
- **Model independence.** Swap JEV or the LLM behind the same contract.
- **Replay and comparison.** Bounded policies can be tested, replayed and benchmarked.
- **Fewer model calls.** Decisions that do not need a full Commander prompt run as a policy.

## 2. Why LAIX, not JEV

JEV answers one closed question. LAIX answers what the task does next.

| JEV | LAIX |
|---|---|
| A judgment | A task decision |
| One model | Composes models and rules |
| Returns an answer and probabilities | Adds constraints, approval, escalation and verification |
| Tied to one engine | One contract across engines |
| One question | One decision shape across decision classes |

JEV is a good policy inside LAIX. Put it there when the judgment must become a task decision with constraints, approval, escalation, verification and a record. That is the work LAIX does.

If PPMA needs one closed judgment, JEV is enough; if it needs the layer around many bounded decisions, LAIX is the layer.

## 3. How they meet

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

PPMA calls LAIX as a tool or task policy inside the Commander or a mission. LAIX returns a `Decision`. PPMA calibrates the confidence it emits, records the decision, commits the outcome and executes.

Deployment:

- a separate `ppma-laix` package or service;
- imports `laix` core and `ppma-contracts`;
- exposes `laix.decide` as an `effect: none` query tool or a mission tool;
- one `DecisionRequest` in, one `Decision` out.

## 4. The interface

| PPMA supplies | LAIX returns |
|---|---|
| Subject and moment | Verb and reason code |
| Situation and options, or signals and context | Confidence, score and breakdown |
| Goals, beliefs and constraints | Evidence, alternatives and constraints applied |
| Attributes and confidence source | Action id, intent, approval and reversibility |

PPMA supplies the task. LAIX returns the decision. PPMA acts on it.

PPMA records the LAIX decision id as a reference and calibrates the confidence it emits. LAIX confidence is a source estimate.

## 5. First proof

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

## 6. One-slide version

```text
PPMA + LAIX — the task-decision layer

PPMA   → activation, memory, calibration, commit, execution
LAIX   → one task decision: wait / observe / guide / ask / act / verify / escalate
JEV    → judgment engine inside a LAIX policy

Why LAIX:
- decision, not just a judgment
- constraints, approval, escalation, verification
- JEV, LLM and deterministic rules compose in one policy
- one contract across decision classes
- model independence, replay and comparison
- fewer model calls for bounded decisions

Start: one bounded decision class. Measure calls, latency, determinism, quality.
```
