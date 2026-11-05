# Examples

Each example demonstrates one LAIX capability and prints a short result. The
folder is organized by language and then by the decision lifecycle:

```text
examples/
├── python/
│   ├── 01-decide/       signals, situations, actions and the core call
│   ├── 02-policies/     packaged policies, authoring, planning, group and shadow
│   ├── 03-plan/         utility, MDP, POMDP, simulation and engine bench
│   ├── 04-stream/       sessions, windows, flow control, checkpoints and sources
│   ├── 05-execute/      execution, multi-step recovery, records, platform and delivery
│   ├── 06-learn/        outcomes, causal attribution, calibration and model learning
│   ├── 07-prove/        evaluation and LAIX-Bench
│   └── 08-stores/       state, outcome-backed and file-backed stores
└── typescript/
    └── (the same numbered stages)
```

Every Python and TypeScript example is executed by CI. The output shown is the
actual output.

## Run

From the repository root.

Python:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
Get-ChildItem examples/python -Recurse -Filter *.py | ForEach-Object { py $_.FullName }
```

TypeScript:

```powershell
Get-ChildItem examples/typescript -Recurse -Filter *.mts | ForEach-Object {
    node --experimental-strip-types $_.FullName
}
```

A single example:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/python/01-decide/attention_bill_due.py
```

## 01 Decide

| Story | Python | TypeScript | Output |
|---|---|---|---|
| A bill is due tomorrow. | `attention_bill_due.py` | `attention_bill_due.mts` | `guide worth_surfacing 84` |
| The same bill arrives at night. | `attention_quiet_hours.py` | `attention_quiet_hours.mts` | `wait quiet_hours 84.0 True False` / `wait quiet_hours 84 true false` |
| The person dismissed the signal. | `attention_feedback.py` | `attention_feedback.mts` | `wait dismissed` |
| A power plan is below its required load. | `attention_power_plan.py` | — | `guide worth_surfacing 75.0` |
| A sink is about to overflow. | `action_leaking_sink.py` | `action.mts` | `act policy_rule option-close-valve` |
| The same sink, through core `decide`. | `action_core_decide.py` | — | `act policy_rule option-close-valve DEC-...` |
| A bill needs payment and approval. | `action_pay_bill.py` | `action_pay_bill.mts` | `act policy_rule option-pay True` / `true` |
| A parcel is late; a tracking page can settle it. | `action_check_again.py` | — | `observe policy_rule option-check-tracking` |
| No safe valve: the safety boundary escalates. | `action_no_valve.py` | `action_no_valve.mts` | `escalate manager 0.7` |
| An alert assigns an owner with approval. | `action_assign_owner.py` | `action_assign_owner.mts` | `act policy_rule assign-owner True` / `true` |
| A quality reading opens a watch. | `action_open_watch.py` | `action_open_watch.mts` | `guide policy_rule open-watch` |
| A caller supplies its own policy. | `action_custom_policy.py` | — | `wait policy_rule` |

## 02 Policies

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Active perception | `active_perception.py` | `packs.mts` | `observe observe_for_information look-1` |
| Safety-constrained action | `safety_constrained.py` | `packs.mts` | `act safe_action valve` |
| Replanning | `replanning.py` | `packs.mts` | `act replan plan-fast` |
| Allocation | `allocation.py` | `packs.mts` | `act allocate ['a', 'b']` |
| Negotiation | `negotiation.py` | `packs.mts` | `act counter_offer 12.5` |
| Preference elicitation | `preference_elicitation.py` | `packs.mts` | `ask ask_preference q2` |
| Verification | `verification.py` | `packs.mts` | `verify verify_outcome api` |
| Escalation | `escalation.py` | `packs.mts` | `escalate escalate_to_target manager` |
| Time-critical gates | `time_critical.py` | — | `act breaker-dry 0.44` |
| Learned bandit policy | `bandit.py` | `bandit.mts` | `manual automatic 0.75` |
| Authored rules and a target | `authoring.py` | `authoring.mts` | `ask over_limit some ('alice', 'ben')` |
| Group target and private masking | `group.py` | `group_shadow.mts` | `all ('alice', 'ben', 'chris') {'topic': 'math'}` |
| Shadow policy comparison | `shadow.py` | `group_shadow.mts` | `ask 1 act` |
| Commitment planning | `planning.py` | `planning.mts` | `act due_commitment a` |
| Persist a commitment ledger | `planning_store.py` | `planning_store.mts` | `send the draft` |

## 03 Plan

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Utility with hard limits | `utility_engine.py` | `engines.mts` | `act bold 0.75` |
| One-step MDP plan | `mdp_engine.py` | `engines.mts` | `act go 2.8` |
| POMDP belief planning | `pomdp.py` | `pomdp.mts` | `act go 2.8` |
| Compare planners on one scenario | `simulator.py` | `engines.mts` | `right 4.0 1.0` |
| Engine bench baseline | `engine_bench.py` | `engine_bench.mts` | `mdp 4.0 1.0` |
| Constraints, stochastic rollout, POMDP check | `engine_depth.py` | `engine_depth.mts` | `safe blocked by risk:risk-limit` / `s1 1.0` / `s0 0.0 go` |

## 04 Stream

| Story | Python | TypeScript | Output |
|---|---|---|---|
| One event becomes a decision | `stream_session.py` | `stream_session.mts` | `guide worth_surfacing STR-DEMO final` |
| Aggregate events into windows | `windows.py` | `windows.mts` | `['2 events', '1 events']` |
| Cooldown, budget and replay | `flow_control.py` | `flow_control.mts` | `1 0 0 1 1 ['d', 'e']` |
| Save and resume a stream | `checkpoint.py` | `checkpoint.mts` | `True 1 1` / `true 1 a b` |
| Read NDJSON into requests | `sources.py` | `sources.mts` | `a b` |
| Retain malformed source frames | `dead_letter.py` | `dead_letter.mts` | `a b 1 True` |
| Export Prometheus counters | `metrics.py` | `metrics.mts` | `1 True` / `1 true` |

## 05 Execute

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Execute a decision | `execution.py` | `execution.mts` | `executed close the valve` |
| Run steps and compensate | `saga.py` | `saga.mts` | `('first',) ('first',) RuntimeError: boom` |
| Bridge execution with receipts | `execution_saga.py` | `execution_saga.mts` | `('reserve',) ('reserve',) RuntimeError: declined` |
| Perception loop | `live_context.py` | `live_context.mts` | `('motion', 'read-label') ('transcribe',) 2 0.097` |
| Resource admission | `resources.py` | `resources.mts` | `('camera', 'read-page') ('full-audio',)` |
| Platform skills and approvals | `platform_interface.py` | `platform.mts` | `7 skill.started,skill.finished fast True` |
| Delivery port | `delivery.py` | `delivery.mts` | `skipped email` |
| Host adapter | `host_adapter.py` | — | `act valve host-calibrated True reason` |
| Host execution | `host_execution.py` | — | `executed approve the repair True` |
| Proposal lifecycle | `proposal.py` | `proposal.mts` | `pending approved applied undone` |
| Decision record lifecycle | `record.py` | `record.mts` | `executed True` |
| Surface a promise and approve a record | `record_promise.py` | — | `guide worth_surfacing approved` |

## 06 Learn

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Estimate a treatment effect | `causal.py` | — | `1.0 difference-in-means` |
| Build a causal ledger from outcomes | `causal_outcomes.py` | — | `6.0 6.0 6.0` |
| Causal intervals and strata | `causal_strata.py` | `causal_strata.mts` | `1.0 -1.771859 3.771859 ['east', 'west']` |
| Calibration and smoothing | `calibration.py` | `calibration.mts` | `0.9 0.5 0.4 0.5` |
| Learn transitions and rewards | `model_learning.py` | `model_learning.mts` | `{'s1': 1.0} 2.0` / `{"s1":1} 2` |
| Causal attribution and planning | — | `causal_planning.mts` | `1 difference-in-means act a` |

## 07 Prove

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Run LAIX-Bench | `bench.py` | `bench.mts` | `25 25 1.0` / `25 25 1` |
| Compare cases with the parity harness | `evaluation.py` | `evaluation.mts` | `2 2 1.0` / `2 2 1` |

## 08 Stores

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Save and load experience state | `state_store.py` | `state_store.mts` | `decide True` / `decide true` |
| Record a measured outcome | `outcome_store.py` | `outcome_store.mts` | `helped -2.0 1` / `helped -2 1` |
| Persist checkpoint and commitment files | `file_stores.py` | `file_stores.mts` | `1 send the draft` |

## Parity notes

Python keeps one story per file. Some TypeScript files intentionally cover
several Python stories:

- `02-policies/packs.mts` covers the eight packaged policies.
- `01-decide/action.mts` covers the main action path.
- `02-policies/group_shadow.mts` covers group and shadow.
- `06-learn/causal_planning.mts` covers causal attribution and planning.

Some Python files remain narrative variants rather than separate TypeScript
capabilities. The test suite is the source of truth for behavioural parity.

## Output meanings

### `guide worth_surfacing 84`

- `guide` — show the item now.
- `worth_surfacing` — the rule that says it is worth showing.
- `84` — the policy score.

### `act policy_rule option-close-valve`

- `act` — do something now.
- `policy_rule` — a written policy rule made the choice.
- `option-close-valve` — the chosen action.

### `wait quiet_hours 84.0 True False`

- `wait` — stay silent now.
- `quiet_hours` — quiet hours are active.
- `84.0` — the score still says it is important.
- `True` — keep it on record for the morning digest.
- `False` — hold it for later.

### `executed True`

- `executed` — the record moved from approved to executed.
- `True` — the record fingerprint still matches its content.

The full field list is in [`../docs/02-core/01-decision-contract.md`](../docs/02-core/01-decision-contract.md).
The policy contracts are in [`../docs/02-core/03-policies.md`](../docs/02-core/03-policies.md).
