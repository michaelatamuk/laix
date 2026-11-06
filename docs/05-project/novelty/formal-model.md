# Formal model and invariants

This page defines the contribution precisely and states the properties the
paper will claim. All formulas match the implementation in `core/engines/planners/`.

## 1. Types

### DecisionProblem

| Field | Type | Meaning |
|---|---|---|
| `subject` | `str` | what the task is about |
| `at` | ISO-8601 | wall-clock time of the decision |
| `situation` | `Situation \| None` | active constraints |
| `options` | `tuple[ActionOption, ...]` | candidate actions |
| `signals` | `tuple[Signal, ...]` | attention signals (attention class) |
| `context` | `Context \| None` | quiet hours and other context |
| `attributes` | `dict` | domain-specific inputs (commitments, budgets, receipts) |

### ActionOption

| Field | Type | Default | Meaning |
|---|---|---|---|
| `id` | `str` | — | unique id |
| `verb` | Verb | `"act"` | intended move |
| `expected_benefit` | `float` | `0.0` | raw benefit estimate |
| `cost` | `float` | `0.0` | direct cost |
| `risk` | `float` | `0.0` | probability × impact |
| `interrupt_cost` | `float` | `0.0` | fractional attention cost |
| `latency_ms` | `float` | `0.0` | expected execution latency |
| `reversible` | `bool` | `True` | can the action be undone? |
| `requires_approval` | `bool` | `False` | needs explicit approval? |
| `params` | `dict` | `{}` | commitment effects, execution facts |

### Commitment

| Field | Type | Meaning |
|---|---|---|
| `id` | `str` | unique id |
| `subject` | `str` | what was promised |
| `due` | ISO-8601 | deadline |
| `status` | `"open" \| "done" \| "cancelled"` | current state |
| `priority` | `float ∈ [0,1]` | importance (default `0.5`) |
| `depends_on` | `tuple[str, ...]` | ids that must be `done` first |

### AttentionBudget

| Field | Type | Meaning |
|---|---|---|
| `total` | `float` | maximum attention available |
| `spent` | `float` | attention already consumed |
| `remaining` | `float` | `total - spent` |

### Plan (planner output)

| Field | Type | Meaning |
|---|---|---|
| `verb` | Verb | chosen move |
| `action_id` | `str \| None` | chosen option id |
| `confidence` | `float ∈ [0,1]` | gap-based confidence |
| `score` | `float` | total score of the chosen option |
| `reason_code` | `str` | structured reason |
| `rationale` | `str` | human-readable explanation |
| `alternatives` | `tuple[dict, ...]` | all other options with their scores |
| `attributes` | `dict` | per-term scores and state |

### Decision (public contract)

Derived from `Plan` via `EnginePolicy`. Every planner returns the same
`Decision` shape regardless of which policy or engine produced it.

## 2. Score composition

`LiveDecisionEngine` computes four additive terms for each option and chooses
the option with the highest total:

```
total(o) = utility(o) + commitment(o) + execution(o) + attention(o)
```

### 2.1 Utility score

```
utility(o) =
    w_benefit   × o.expected_benefit
  - w_cost      × o.cost
  - w_risk      × risk_adj(o.risk, attitude)
  - w_interrupt × o.interrupt_cost
  - w_latency   × o.latency_ms
```

**Risk adjustment** by `risk_attitude`:

| Attitude | Formula |
|---|---|
| `neutral` | `risk` |
| `averse` | `risk × (1 + risk)` |
| `seeking` | `risk × (1 - 0.5 × risk)` |

**Default weights** (`UtilityWeights`):

| Weight | Default |
|---|---|
| `benefit` | 1.0 |
| `cost` | 0.25 |
| `risk` | 0.25 |
| `interruption` | 0.15 |
| `latency` | 0.0 |

**Hard feasibility gates** (applied before scoring; infeasible options are excluded):

- `o.risk > model.max_risk` → infeasible
- `o.cost > model.max_cost` → infeasible (when set)
- `o.latency_ms > model.max_latency_ms` → infeasible (when set)
- `Constraint(hard=True, kind="risk", value=r)` and `o.risk > r` → infeasible

### 2.2 Commitment score

Let `open` = `{c.id | c.status == "open"}` and `at` = decision time.

```
commitment(o) =
  + Σ  w_keep    × (0.5 + c.priority)   for c in fulfills(o) ∩ open, not blocked(c)
  + Σ  w_due     × (0.5 + c.priority)   for c in fulfills(o) ∩ open ∩ due(at)
  - Σ  w_violate × (0.5 + c.priority)   for c in violates(o) ∩ open
  - Σ  w_due     × (0.5 + c.priority)   for c in violates(o) ∩ open ∩ due(at)
  - w_blocked × |fulfills(o) ∩ open ∩ blocked|
  - w_create  × |creates(o) \ existing|
```

Where `blocked(c)` = any dependency of `c` is still `"open"`.

If `commitment.hard == True` and `c ∈ violates(o) ∩ open` → option is blocked (infeasible).

**Default weights** (`CommitmentWeights`):

| Weight | Default |
|---|---|
| `keep` | 0.35 |
| `violate` | 1.0 |
| `create` | 0.10 |
| `due` | 0.25 |
| `blocked` | 0.50 |

### 2.3 Execution score

```
execution(o) =
  - w_irreversible   if o.reversible == False
  - w_unknown        × unknown_risk(o)
  - w_approval       if o.requires_approval == True and not pre-approved
  - w_recovery       × recovery_cost(o)
```

`unknown_risk` and `recovery_cost` are read from `o.params["execution"]` or
the host's `execution_state` receipts.

**Default weights** (`ExecutionWeights`):

| Weight | Default |
|---|---|
| `irreversible` | 0.35 |
| `unknown` | 0.5 |
| `approval` | 0.15 |
| `recovery` | 0.25 |

### 2.4 Attention score

Let `remaining` = `budget.total - budget.spent`.

```
attention(o) =
  - w_interrupt   × o.interrupt_cost
  - w_approval    if o.requires_approval == True and not pre-approved
  - w_escalation  if o.verb == "escalate"
  - w_exhausted   if blocked == "attention budget exhausted"
```

An option is blocked (`"attention budget exhausted"`) when `effect.requires_attention`
is true and `effect.cost > remaining`.

**Default weights** (`AttentionWeights`):

| Weight | Default |
|---|---|
| `interrupt` | 0.4 |
| `approval` | 0.25 |
| `escalation` | 0.3 |
| `exhausted` | 1.0 |

### 2.5 Selection and confidence

```
chosen = argmax_{o ∈ feasible} total(o)
         tie-break: lexicographic on option id

confidence(best, second) =
    1.0                                       if no second option exists
    clamp(0.5 + 0.5 × gap / |best|)          otherwise, gap = max(0, best - second)
```

If no feasible option exists, the planner returns `verb = "wait"` with
`reason_code = "no_feasible_option"`.

### 2.6 Ablation results (live bench, 7 cases)

Reproducible by running `examples/python/03-plan/ablation_study.py`.

| Planner | Correct / 7 | Accuracy |
|---|---:|---:|
| `first` | 3 | 43% |
| `benefit` | 1 | 14% |
| `utility` | 2 | 29% |
| `commitment` | 3 | 43% |
| `execution` | 5 | 71% |
| `attention` | 4 | 57% |
| **live** | **7** | **100%** |

The integration adds real value: each single-concern planner wins its own
cases but fails on cases where two or more concerns fire simultaneously.
See `examples/python/03-plan/conflict_scenario.py` for a worked example.

## 3. State machines

### Receipt state machine

```
              ┌──────────┐
    ┌─────────► approved ├────────────────────┐
    │         └────┬─────┘                    │
    │              │ run                       │
┌───┴─────┐  ┌────▼──────┐  ┌────────┐       │
│ pending │  │ executed  ├─►│ undone │       │
└───┬─────┘  └────┬──────┘  └────────┘       │
    │              │                           │
    │         ┌────▼──────┬──────────┐        │
    │         │  failed   │cancelled │        │
    └────────►│  refused  │ unknown  ◄────────┘
              └───────────┴──────────┘
```

`duplicate` is a parallel status set when the same `idempotency_key` is seen
again; it does not change the main state.

### Revision state machine (Timeline)

```
revision 0  (initial)
     │
     ▼
revision 1  (revised_from = decision_id_0, event_time ≥ event_time_0)
     │
     ▼
revision N  (revised_from = decision_id_{N-1}, event_time ≥ event_time_{N-1})
```

A `Timeline` is append-only. `event_time` never decreases.

## 4. Invariants

The following must hold at all times. Tests live in
`tests/core/test_invariants.py`.

| ID | Invariant |
|---|---|
| I1 | **Determinism** — the same `DecisionProblem` and planner configuration always produce the same `Plan`. |
| I2 | **Hard constraint gate** — an option whose `risk` exceeds a hard risk constraint is never the chosen action. |
| I3 | **Attention budget** — an option with `attention_cost > remaining` that `requires_attention` is never chosen. |
| I4 | **Rejected approval** — an option with `approval_state = "rejected"` is never chosen. |
| I5 | **Revision monotonicity** — `revision > 0` implies non-null `revised_from`; `event_time` never decreases across revisions in a `Timeline`. |
| I6 | **Receipt state machine** — no invalid receipt transition is allowed; the receipt status follows the diagram in §3. |
| I7 | **Trace append-only** — `Trace.with_event` appends an event and never removes an existing event. |
| I8 | **Confidence bounds** — `plan.confidence ∈ [0.0, 1.0]` for every plan returned by any planner. |
| I9 | **Contract consistency** — `EnginePolicy(engine).decide(req)[0]` and `decide(req, policy=EnginePolicy(engine))[0]` return decisions with the same `verb`, `action_id`, `reason_code` and `score`. |
| I10 | **Parity infrastructure** — the shared conformance schema and parity tests are present; full verb parity is checked by `tests/test_language_parity.py` and the TypeScript suite. |

## 5. Acceptance criteria

- Every invariant in §4 has a test in `tests/core/test_invariants.py` that
  fails if the code regresses.
- The score formulas in §2 match the source in `core/engines/planners/`.
- The ablation table in §2.6 is reproducible by running
  `examples/python/03-plan/ablation_study.py` with one command.
