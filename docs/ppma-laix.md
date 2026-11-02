# PPMA + LAIX: the task-decision layer

PPMA decides what a trigger becomes. LAIX decides what one bounded task does next.

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Question | What does this trigger become? | What is the next move for this task? |
| Output | `NOOP` · `UPDATE_STATE` · `ISSUE_COMMAND` · `DISPATCH` | `wait` · `observe` · `guide` · `ask` · `act` · `verify` · `escalate` |
| Scope | PPMA's next cycle | One bounded task |

## 1. What LAIX decides

A LAIX policy is a small object with a `name` and a `decide(request)` method. It can use deterministic rules, a model judgment, or both. It receives a bounded task and returns one decision:

- `verb`: `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`;
- `reason_code` and `rationale`;
- `confidence`, `score` and `breakdown`;
- `action_id` and `intent`;
- `requires_approval`, `reversible` and `undo_hint`;
- `decision_id`.

Example:

```text
Task: a customer asks for a €780 refund.
Options: send_reply (act), ask_owner (ask), wait.
Constraints: refunds above €500 need owner approval; VIP complaints escalate.
Attributes: amount_eur = 780, vip = true.

LAIX returns:
  verb = ask
  reason_code = over_approval_limit
  action_id = send_reply
  requires_approval = true
  confidence = 0.92
  decision_id = DEC-...
```

PPMA issues `ui.ask`, records the decision, commits the outcome and acts.

## 2. Who owns what

| Area | Owner |
|---|---|
| Trigger and activation decision | PPMA |
| Memory, connectors, permissions, proactivity | PPMA |
| Flow policy, holding and app execution policy | PPMA |
| Task goal, options and constraints | PPMA |
| Task decision | LAIX |
| Policy composition and decision semantics | LAIX |
| Calibration, provenance, commit and execution | PPMA |

PPMA supplies the task. LAIX returns the decision. PPMA acts on it.

## 3. Why PPMA uses it

- **One task-decision contract** across the Commander, missions and apps.
- **Decision semantics** — constraints, approval, escalation and verification travel with the decision.
- **Policy composition** — models and deterministic rules sit inside one policy.
- **Fewer model calls** — a bounded decision that does not need a full Commander prompt runs as a policy.
- **Replay and comparison** — policies can be tested, replayed and benchmarked.
- **Model independence** — swap the model behind the same contract.
- **Reuse without Core changes** — a policy lives outside `ppma.core`; PPMA adds decision classes without new Core modules.

## 4. How the call works

```text
PPMA trigger
  → Commander / ActivationDecision
  → bounded task
  → LAIX task policy
       reads    situation · options · constraints
       applies  rules, model judgment, or both
       returns  decision — verb · reason · confidence · action · approval
  → PPMA calibrates, records, commits, executes
```

PPMA calls LAIX as a tool or task policy inside the Commander or a mission. LAIX returns a `Decision`. PPMA calibrates the confidence it emits, records the decision, commits the outcome and executes.

Deployment:

- a separate `ppma-laix` package or service;
- imports `laix` core and `ppma-contracts`;
- exposes `laix.decide` as an `effect: none` query tool or a mission tool;
- one `DecisionRequest` in, one `Decision` out.

PPMA implements four things:

- a manifest entry for `laix.decide` with `effect: none`;
- an adapter from the bounded task to `DecisionRequest`;
- an adapter from `Decision` to the PPMA command, ask or dispatch;
- calibration, provenance and commit around the result.

Interface:

| PPMA supplies | LAIX returns |
|---|---|
| Subject and moment | Verb and reason code |
| Situation and options, or signals and context | Confidence, score and breakdown |
| Goals, beliefs and constraints | Evidence, alternatives and constraints applied |
| Attributes and confidence source | Action id, intent, approval and reversibility |

PPMA records the LAIX decision id as a reference. LAIX confidence is a source estimate; PPMA emits the calibrated confidence.

## 5. First proof

Start with one bounded decision class:

- a mission step; or
- a Commander subtask that currently needs a full LLM ask.

Implement it as a LAIX policy with a model judgment when needed. Expose it as an `effect: none` tool or a mission tool.

Measure:

- model calls and tokens;
- latency;
- determinism and replay;
- decision quality;
- audit clarity.

Use the result to choose the next decision class.

## 6. If you already use a judgment model

JEV is a judgment engine: one closed question in, an answer with probabilities out. It can sit inside a LAIX policy.

Put it there when the judgment must become a task decision with constraints, approval, escalation, verification and a record. That is the work LAIX does.

If you need one closed judgment, JEV is enough. When you need the layer around many bounded decisions, LAIX is the layer.

## 7. One-slide version

```text
PPMA + LAIX — the task-decision layer

PPMA   → trigger, activation, memory, calibration, commit, execution
LAIX   → one task decision: verb, reason, confidence, action, approval

Example: €780 refund → ask, over_approval_limit, requires_approval

Why LAIX:
- one task-decision contract across Commander, missions and apps
- constraints, approval, escalation, verification
- models and deterministic rules compose in one policy
- fewer model calls for bounded decisions
- replay, comparison and model independence
- reuse without Core changes

Start: one bounded decision class. Measure calls, latency, determinism, quality.
```
