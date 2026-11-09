# PPMA integration: the task-decision layer

PPMA (the activation layer above LAIX; see the [glossary](../../05-reference/01-glossary.md)) decides what
the system does next. LAIX decides what one task does next.

The generic boundary is in [Scope and boundaries](../01-architecture/02-scope-and-boundaries.md). This
page is the PPMA-specific path.

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
Request
  task               a customer asks for a €780 refund
  options            send_reply (act) · ask_owner (ask) · wait
  constraints        refunds above €500 need owner approval; VIP complaints escalate
  attributes         amount_eur = 780, vip = true

Decision
  verb               ask
  reason_code        over_approval_limit
  action_id          send_reply
  requires_approval  true
  confidence         0.92
  decision_id        DEC-...
```

PPMA issues `ui.ask`, records the decision, commits the outcome and acts.

## 2. How PPMA decides

PPMA reaches an activation decision through four paths. It names its edges by compass: **north** is apps, **south** is what PPMA runs on (model vendors and their adapters), **east** is third-party agents that PPMA delegates work to, and **west** is agents that consult memory.

Every activation decision is one of four kinds: `NOOP` (no operation), `UPDATE_STATE` (a memory change), `ISSUE_COMMAND` (one or more commands), or `DISPATCH` (start a mission).

| Path | Edge | How | Output |
|---|---|---|---|
| `Commander.wake()` | South | One `command.decide` LLM ask | `NOOP`, `UPDATE_STATE`, `ISSUE_COMMAND` or `DISPATCH` |
| `Commander.exit_check()` | South | One `command.exit_check` LLM ask for a due entry | `UPDATE_STATE` or `NOOP` |
| `Commander.effect_step()` | Timer | A scheduled command is re-checked and issued | `ISSUE_COMMAND` |
| Mission agent | East | An agent run on JiuwenSwarm, Claude Code or another harness | A proposal (`DispatchResult`); PPMA turns it into a command |

The `command.decide` ask is the general chooser: it picks the commands, dispatch, plans, filters and missions. The other three paths handle a narrower case.

An effect step is a scheduled command. The command was chosen by the `command.decide` ask when the plan was installed; the timer executes it. When the timer fires, PPMA re-checks it against the current manifests, permissions, holders and health rules and issues it as `ISSUE_COMMAND`. Fire time stays deterministic.

A mission agent returns a proposal; PPMA turns it into a command. Its `DispatchResult` carries the
report, evidence and artifacts it produced, plus an optional state delta. PPMA reviews it before
committing.

PPMA's core rules and filters validate, constrain, hold and calibrate the command.

## 3. The PPMA-LAIX boundary

### What each decides

The two decisions differ in vocabulary and scope:

| | PPMA activation decision | LAIX task decision |
|---|---|---|
| Kind | `NOOP` · `UPDATE_STATE` · `ISSUE_COMMAND` · `DISPATCH` | `wait` · `observe` · `guide` · `ask` · `act` · `verify` · `escalate` |
| Scope | Across the system | Inside one task |

The mapping from a LAIX verb to a command is many-to-many. PPMA chooses the command type and target
from the task move, the available manifests and the execution policy. A `guide` decision may become
`ui.notify`, `ui.deliver_brief` or an app-specific message; an `act` decision may become a manifest
tool, a plan step or a `DISPATCH`.

### What each side owns

| Area | Owner |
|---|---|
| Incoming input and activation decision | PPMA |
| Memory, connectors, permissions, proactivity | PPMA |
| Flow policy, holding and app execution policy | PPMA |
| Task goal, options and constraints | PPMA |
| Task decision | LAIX |
| DecisionPolicy composition and decision semantics | LAIX |
| Calibration, provenance, commit and execution | PPMA |

## 4. Why PPMA should use LAIX

LAIX adds a policy path alongside the Commander. For a bounded decision class, compare a LAIX policy with the Commander's `command.decide` ask on calls and tokens, latency, determinism, constraint compliance, audit clarity and reuse. If the policy improves on none of them, keep the Commander.

The difference is clearest in latency. PPMA's command choice is taken when the model answers: `command.decide` is an LLM ask. A rules-only LAIX policy decides locally; a model-backed policy pays the model, on a smaller question. For a decision taken inside a loop, that is the difference that matters.

It also adds:

- **One task-decision contract** across the Commander, missions and apps.
- **Decision semantics** - constraints, approval, escalation and verification travel with the decision.
- **DecisionPolicy composition** - models and deterministic rules sit inside one policy.
- **Fewer model calls** - a bounded decision that fits a policy runs as a policy.
- **Replay and comparison** - policies can be tested, replayed and benchmarked.
- **Model independence** - swap the model behind the same contract.
- **Reuse without Core changes** - a policy lives outside `ppma.core`; PPMA adds decision classes without new Core modules.

## 5. How PPMA would call LAIX

```text
PPMA input
  → Commander / ActivationDecision
  → bounded task
  → LAIX task policy
       reads    situation · options · constraints
       applies  rules, model judgment, or both
       returns  decision - verb · reason · confidence · action · approval
  → PPMA calibrates, records, commits, executes
```

The integration calls LAIX as a tool or task policy inside the Commander or a mission. The call uses PPMA's existing Commander or mission path; JEV and LLM calls stay with PPMA's engines or the policy adapter.

Deployment:

- a separate `ppma-laix` package or service;
- imports the `laix.decision` package and `ppma-contracts`;
- exposes `laix.decide` as an `effect: none` query tool or a mission tool;
- one `DecisionRequest` in, one `Decision` out.

The integration adds four things:

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
| Attributes and confidence source | `action_id`, intent, approval and reversibility |

PPMA records the LAIX decision id as a reference. LAIX confidence is a source estimate; PPMA emits the calibrated confidence.

## 6. If you already use a judgment model

JEV gives you the judgment - one closed question in, an answer with probabilities out. LAIX gives you the decision: the move, reason, action, approval, reversibility, verification and record, under the same contract across tasks. JEV can sit inside a LAIX policy.

### Example: paying a supplier invoice

**JEV alone.** Ask JEV the task question directly:

```text
Pay, hold, ask or escalate this invoice?
→ pay, 0.87
```

That is a proposed move; LAIX turns it into a decision. JEV returns a probability over options. LAIX
adds the reason code, action, approval flag, reversibility, verification step and decision record.

**JEV inside a LAIX policy.** The invoice is €4,800, above the €2,000 approval limit. Payment is irreversible. The supplier is new. The policy takes the JEV answer plus the options and constraints and returns:

```text
verb = ask
reason_code = over_approval_limit
action_id = pay_invoice
requires_approval = true
reversible = false
confidence = 0.95
```

The judgment said `pay`; the limit says `ask`. The policy applies the rule with precedence and the
decision records why. A prompt can carry the limit too; a policy makes it a rule that fires whenever
the condition holds. The judgment still carries the PO match, the new supplier and the delivery.

PPMA issues `ui.ask`, records the decision, pays on approval and verifies the bank confirmation.

### JEV alone or with LAIX

**Use JEV alone when** the output is one judgment and the app already knows what to do with it. App code can add approval, reversibility, verification and the record for one task; the second task writes them again, and the copies drift - one gates in the UI, another in a flag, a third forgets `reversible`.

**Use JEV with LAIX when** the judgment must become a task decision with constraints, approval, escalation, verification and a record. LAIX supplies it once, under the same contract across tasks.
