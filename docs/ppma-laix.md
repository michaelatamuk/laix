# PPMA + LAIX: the task-decision layer

PPMA decides what a trigger becomes. LAIX decides what one bounded task does next.

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

## 2. Two decision scopes

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Question | What does this trigger become? | What is the next move for this task? |
| Kind | `NOOP` · `UPDATE_STATE` · `ISSUE_COMMAND` · `DISPATCH` | `wait` · `observe` · `guide` · `ask` · `act` · `verify` · `escalate` |
| Scope | PPMA's next cycle | One bounded task |

The two vocabularies describe different scopes.

- `NOOP`: no action.
- `UPDATE_STATE`: a memory change.
- `ISSUE_COMMAND`: one or more commands to apps or tools.
- `DISPATCH`: start a mission.

`ISSUE_COMMAND` carries one or more commands. The mapping from a LAIX verb to a command is not one-to-one: PPMA chooses the command type and target from the task move, the available manifests and the execution policy. A `guide` decision may become `ui.notify`, `ui.deliver_brief` or an app-specific message; an `act` decision may become a manifest tool, a plan step or a `DISPATCH`. LAIX returns the task move; PPMA chooses the command and issues it.

## 3. Who owns what

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

### How PPMA decides today

| Path | What it does |
|---|---|
| `Commander.wake()` | One `command.decide` LLM ask. It chooses the commands, dispatch, plans, filters and missions. |
| `Commander.exit_check()` | One `command.exit_check` LLM ask for an entry whose `until` passed. |
| `Commander.effect_step()` | A plan's pre-approved step issues its stored command. No model call; the decision was made when the plan was installed. |
| Mission agent | The agent decides inside its bounded mission. PPMA reviews the proposal. |
| Core rules and filters | They validate, constrain, calibrate or hold. They do not choose a command. |

Today the Commander's `command.decide` ask is the only general command chooser. LAIX adds a policy path for bounded task decisions alongside it. The comparison is Commander alone vs Commander + LAIX for one bounded decision class.

## 4. Why PPMA uses it

- **One task-decision contract** across the Commander, missions and apps.
- **Decision semantics** — constraints, approval, escalation and verification travel with the decision.
- **Policy composition** — models and deterministic rules sit inside one policy.
- **Fewer model calls** — a bounded decision that does not need a full Commander prompt runs as a policy.
- **Replay and comparison** — policies can be tested, replayed and benchmarked.
- **Model independence** — swap the model behind the same contract.
- **Reuse without Core changes** — a policy lives outside `ppma.core`; PPMA adds decision classes without new Core modules.

## 5. How the call works

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

## 6. First proof

Pick one bounded decision class where the Commander currently uses an LLM ask — a mission step or a Commander subtask. Implement it as a LAIX policy and expose it as an `effect: none` tool. Measure calls, latency, determinism and decision quality. Extend where it wins.

## 7. If you already use a judgment model

JEV is a judgment engine: one closed question in, an answer with probabilities out. It can sit inside a LAIX policy.

Put it there when the judgment must become a task decision with constraints, approval, escalation, verification and a record. That is the work LAIX does.

If you need one closed judgment, JEV is enough. When you need the layer around many bounded decisions, LAIX is the layer.

## 8. One-slide version

```text
PPMA + LAIX — the task-decision layer

PPMA   → trigger, activation, memory, calibration, commit, execution
LAIX   → one task decision: verb, reason, confidence, action, approval

Today: Commander LLM ask chooses commands.
With LAIX: a policy path for one bounded decision class.

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
