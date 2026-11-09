# Examples

Each example demonstrates one LAIX capability and prints a short result. The folder follows the same
split as the package:

```text
examples/
├── data/                  decision JSON for the CLI
├── mcp/                   MCP client config and tool example
├── python/
│   ├── decision/
│   │   ├── domain/
│   │   │   ├── planning_store      promise and ledger persistence
│   │   │   └── outcome_store       measured outcomes and stores
│   │   ├── decision/
│   │   │   ├── single/
│   │   │   │   ├── decide/       signals, situations, actions and the decision layer call
│   │   │   │   ├── policies/     packaged, authored and learned policies
│   │   │   │   └── planners/     utility, commitment, execution, attention, CA-VOD, MDP, POMDP
│   │   │   ├── sequence/         CABB, rollout and replan
│   │   │   ├── fleet/            attention scheduling and the Whittle index
│   │   │   ├── history/          continuity repair
│   │   │   └── explain/          counterfactual attribution and search
│   │   ├── sensing/
│   │   │   ├── signals/          signal attention and quiet hours
│   │   │   └── resources.py      resource admission and sensing
│   │   ├── learning/
│   │   │   ├── calibration/      prediction and decision calibration
│   │   │   ├── model/            learned transitions
│   │   │   └── causal/           treatment and control effects
│   │   └── evaluation/
│   │       ├── cases/            parity harness and shadow rollout
│   │       ├── bench/            live benchmark, planner bench and ablation
│   │       └── simulation/       simulator and planner depth
│   └── appkit/
│       ├── build/                host adapter and policy registry
│       ├── run/                  stream, windows, checkpoints, live context and live loop
│       ├── execute/              execution, reliability, action profile, saga, record and proposal
│       ├── connect/              platform, delivery, state/outcome files and stores
│       └── operate/              LAIX-Bench, metrics and OpenTelemetry
└── typescript/
    └── (the same decision and app-kit split)
```

Every Python and TypeScript example is executed by CI. The output shown is the actual output.

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
py examples/python/decision/sensing/signals/signal_attention_bill_due.py
```

# Decision

## Domain

### Commitments

`examples/python/decision/domain/` · `examples/typescript/decision/domain/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Persist a commitment ledger | `planning_store.py` | `planning_store.mts` | `send the draft` |
| Reason across owners and trust | `commitment_graph.py` | `commitment_graph.mts` | `unverified supplier ship` |
| Resolve a foreign commitment | `commitment_resolver.py` | `commitment_resolver.mts` | `wait finish` |
| Freshness changes the decision | `commitment_freshness_bench.py` | `commitment_freshness_bench.mts` | `5/5` |

### Outcomes

`examples/python/decision/domain/` · `examples/typescript/decision/domain/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Record a measured outcome | `outcome_store.py` | `outcome_store.mts` | `helped -2.0 1` / `helped -2 1` |

## Decision

### Single decision: decide

`examples/python/decision/decision/single/decide/` · `examples/typescript/decision/decision/single/decide/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| A sink is about to overflow. | `action_leaking_sink.py` | `action.mts` | `act policy_rule option-close-valve` |
| The same sink, through `decide`. | `action_decide.py` | — | `act policy_rule option-close-valve DEC-...` |
| A bill needs payment and approval. | `action_pay_bill.py` | `action_pay_bill.mts` | `act policy_rule option-pay True` / `true` |
| A parcel is late; a tracking page can settle it. | `action_check_again.py` | — | `observe policy_rule option-check-tracking` |
| No safe valve: the safety boundary escalates. | `action_no_valve.py` | `action_no_valve.mts` | `escalate manager 0.7` |
| An alert assigns an owner with approval. | `action_assign_owner.py` | `action_assign_owner.mts` | `act policy_rule assign-owner True` / `true` |
| A quality reading opens a watch. | `action_open_watch.py` | `action_open_watch.mts` | `guide policy_rule open-watch` |

### Single decision: policies

`examples/python/decision/decision/single/policies/` · `examples/typescript/decision/decision/single/policies/`

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
| A caller supplies its own policy. | `action_custom_policy.py` | — | `wait policy_rule` |

### Single decision: planners

`examples/python/decision/decision/single/planners/` · `examples/typescript/decision/decision/single/planners/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Utility with hard limits | `utility_planner.py` | `planners.mts` | `act bold 0.75` |
| Commitment-aware planning | `commitment_planner.py` | `commitment_planner.mts` | `send-later commitment_aware c1` |
| Execution-aware planning | `execution_planner.py` | `execution_planner.mts` | `archive execution_aware True` / `true` |
| Human-attention planning | `human_attention_planner.py` | `human_attention_planner.mts` | `act human_attention_aware 0.0` / `0` |
| Live composite planner | `live_composite_planner.py` | `live_composite_planner.mts` | `safe live_decision c1` |
| One-step MDP plan | `mdp_planner.py` | `planners.mts` | `act go 2.8` |
| POMDP belief planning | `pomdp_planner.py` | `pomdp_planner.mts` | `act go 2.8` |
| CA-VOD information and option value | `ca_vod_planner.py` | `ca_vod_planner.mts` | `ask value_of_decision 0.28 0.0` / `ask value_of_decision 0.28 0` |
| CA-VOD belief-state future value | `ca_vod_belief.py` | `ca_vod_belief.mts` | `ask 0.45 2` |

### Sequence

`examples/python/decision/decision/sequence/` · `examples/typescript/decision/decision/sequence/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Exact sequence planning, rollout and replan | `sequence_planning.py` | `sequence_planning.mts` | `ask,verify 1.49 True ask,verify verify` / `ask,verify 1.49 true ask,verify verify` |
| Exact planning beats greedy rollout | `sequence_tradeoff.py` | `sequence_tradeoff.mts` | `cabb start,small,bonus 1.105` / `rollout start,big,nothing 0.605` |

### Fleet

`examples/python/decision/decision/fleet/` · `examples/typescript/decision/decision/fleet/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| AADS attention schedule | `attention_scheduler.py` | `attention_scheduler.mts` | `refund-approval,check-evidence` / `1.5 1.5` |
| AADS exact Whittle index | `whittle_scheduler.py` | `whittle_scheduler.mts` | `0.9 0.09` / `high low` |

### History

`examples/python/decision/decision/history/` · `examples/typescript/decision/decision/history/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| CDR continuity repair | `continuity_repair.py` | `continuity_repair.mts` | `approval-1 supersede 1.0` |
| CDR exact minimum-cost repair | `continuity_repair_exact.py` | `continuity_repair_exact.mts` | `3.0 2.0 ['b']` / `3 2 [ 'b' ]` |
| Three concerns in one scenario | `conflict_scenario.py` | — | `LiveCompositePlanner wins every case` |

### Explain

`examples/python/decision/decision/explain/` · `examples/typescript/decision/decision/explain/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| CDA counterfactual attribution | `counterfactual_attribution.py` | `counterfactual_attribution.mts` | `ask wait commitment 0.970001` |
| CDA counterfactual search | `counterfactual_search.py` | `counterfactual_search.mts` | `act escalate 0.5 0.1` |

## Sensing

### Signals

`examples/python/decision/sensing/signals/` · `examples/typescript/decision/sensing/signals/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| A bill is due tomorrow. | `signal_attention_bill_due.py` | `signal_attention_bill_due.mts` | `guide worth_surfacing 84` |
| The same bill arrives at night. | `signal_attention_quiet_hours.py` | `signal_attention_quiet_hours.mts` | `wait quiet_hours 84.0 True False` / `wait quiet_hours 84 true false` |
| The person dismissed the signal. | `signal_attention_feedback.py` | `signal_attention_feedback.mts` | `wait dismissed` |
| A power plan is below its required load. | `signal_attention_power_plan.py` | — | `guide worth_surfacing 75.0` |

### Resources

`examples/python/decision/sensing/` · `examples/typescript/decision/sensing/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Resource admission | `resources.py` | `resources.mts` | `('camera', 'read-page') ('full-audio',)` |

## Learning

### Calibration

`examples/python/decision/learning/calibration/` · `examples/typescript/decision/learning/calibration/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Calibration and smoothing | `calibration.py` | `calibration.mts` | `0.9 0.5 0.4 0.5` |
| Decision-level calibration | `decision_calibration.py` | `decision_calibration.mts` | `0.9 0.5 decision-calibration` |

### Model

`examples/python/decision/learning/model/` · `examples/typescript/decision/learning/model/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Learn transitions and rewards | `model_learning.py` | `model_learning.mts` | `{'s1': 1.0} 2.0` / `{"s1":1} 2` |
| Restore the best model snapshot | `model_rollback.py` | `model_rollback.mts` | `{'done': 1.0}` / `{ done: 1 }` |

### Causal

`examples/python/decision/learning/causal/` · `examples/typescript/decision/learning/causal/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Estimate a treatment effect | `causal.py` | — | `1.0 difference-in-means` |
| Build a causal ledger from outcomes | `causal_outcomes.py` | — | `6.0 6.0 6.0` |
| Causal intervals and strata | `causal_strata.py` | `causal_strata.mts` | `1.0 -1.771859 3.771859 ['east', 'west']` |
| Causal attribution and planning | — | `causal_planning.mts` | `1 difference-in-means act a` |

## Evaluation

### Cases

`examples/python/decision/evaluation/cases/` · `examples/typescript/decision/evaluation/cases/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Compare cases with the parity harness | `evaluation.py` | `evaluation.mts` | `2 2 1.0` / `2 2 1` |
| Shadow rollout and promotion | `shadow_rollout.py` | — | `2/6 33%` |

### Bench

`examples/python/decision/evaluation/bench/` · `examples/typescript/decision/evaluation/bench/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Training-free live decisions | `live_bench.py` | `live_bench.mts` | `utility 0.29 0` / `commitment 0.43 0` / `execution 0.71 0` / `attention 0.57 0` / `live 1.00 0` |
| Planner bench baseline | `planner_bench.py` | `planner_bench.mts` | `mdp 4.0 1.0` |
| Per-case ablation | `ablation_study.py` | — | `live 7/7` |

### Simulation

`examples/python/decision/evaluation/simulation/` · `examples/typescript/decision/evaluation/simulation/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Compare planners on one scenario | `simulator.py` | `planners.mts` | `right 4.0 1.0` |
| Constraints, stochastic rollout, POMDP check | `planner_depth.py` | `planner_depth.mts` | `safe blocked by risk:risk-limit` / `s1 1.0` / `s0 0.0 go` |

# App kit

## Build

`examples/python/appkit/build/` · `examples/typescript/appkit/build/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Host adapter | `host_adapter.py` | - | `act valve host-calibrated True reason` |
| Register and switch a policy | `policy_registry.py` | `policy_registry.mts` | `safety act valve` |

## Run

`examples/python/appkit/run/` · `examples/typescript/appkit/run/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| One event becomes a decision | `stream_session.py` | `stream_session.mts` | `guide worth_surfacing STR-DEMO final` |
| Aggregate events into windows | `windows.py` | `windows.mts` | `['2 events', '1 events']` |
| Cooldown, budget and replay | `flow_control.py` | `flow_control.mts` | `1 0 0 1 1 ['d', 'e']` |
| Save and resume a stream | `checkpoint.py` | `checkpoint.mts` | `True 1 1` / `true 1 a b` |
| Keep a decision timeline | `decision_timeline.py` | `decision_timeline.mts` | `2 1 d2 d1,d2` |
| Read NDJSON into requests | `sources.py` | `sources.mts` | `a b` |
| Retain malformed source frames | `dead_letter.py` | `dead_letter.mts` | `a b 1 True` |
| Perception loop | `live_context.py` | `live_context.mts` | `('motion', 'read-label') ('transcribe',) 2 0.097` |
| Full loop: stream, decision, execution, outcome, calibration and timeline | `live_loop.py` | `live_loop.mts` | `safe act executed helped 1 0.8 1.0` |

## Execute

`examples/python/appkit/execute/` · `examples/typescript/appkit/execute/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Execute a decision | `execution.py` | `execution.mts` | `executed close the valve` |
| Run steps and compensate | `saga.py` | `saga.mts` | `('first',) ('first',) RuntimeError: boom` |
| Bridge execution with receipts | `execution_saga.py` | `execution_saga.mts` | `('reserve',) ('reserve',) RuntimeError: declined` |
| Host execution | `host_execution.py` | — | `executed approve the repair True` |
| Retry and time out an execution | `reliable_execution.py` | `reliable_execution.mts` | `executed 3 unknown` |
| Map an OpenAPI action profile | `action_profile.py` | `action_profile.mts` | `executed close case` |
| Proposal lifecycle | `proposal.py` | `proposal.mts` | `pending approved applied undone` |
| Decision record lifecycle | `record.py` | `record.mts` | `executed True` |
| Surface a promise and approve a record | `record_promise.py` | — | `guide worth_surfacing approved` |

## Connect

`examples/python/appkit/connect/` · `examples/typescript/appkit/connect/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Platform skills and approvals | `platform_interface.py` | `platform.mts` | `7 skill.started,skill.finished fast True` |
| Delivery port | `delivery.py` | `delivery.mts` | `skipped email` |
| Save and load experience state | `state_store.py` | `state_store.mts` | `decide True` / `decide true` |
| Persist checkpoint and commitment files | `file_stores.py` | `file_stores.mts` | `1 send the draft` |
| Persist state and outcomes as JSON | `file_state_outcome.py` | `file_state_outcome.mts` | `decide 1` |

## Operate

`examples/python/appkit/operate/` · `examples/typescript/appkit/operate/`

| Story | Python | TypeScript | Output |
|---|---|---|---|
| Run LAIX-Bench | `bench.py` | `bench.mts` | `25 25 1.0` / `25 25 1` |
| Export Prometheus counters | `metrics.py` | `metrics.mts` | `1 True` / `1 true` |
| Map a decision to OTel attributes | `otel.py` | `otel.mts` | `act safe_action valve True` / `act safe_action valve true` |

## Tools

### CLI

```powershell
laix explain examples/data/decision.json
laix lint examples/data/decision.json
```

`laix explain` prints the decision fields. `laix lint` exits non-zero when an audit field is
missing. The test suite covers both.

### MCP

`examples/mcp/client-config.json` is a ready MCP client entry. It launches `laix-mcp` over stdio.
See [the MCP guide](../docs/03-appkit/01-build/05-mcp.md) for the tool request and install.

### A2A and OpenAPI

The A2A card and OpenAPI action profile are contracts, not runnable examples:

- `packages/contracts/a2a-agent-card.v1.json`
- `packages/contracts/action.openapi.v1.json`

See [A2A and OpenAPI](../docs/03-appkit/01-build/06-a2a.md).

## Parity notes

Python keeps one story per file. Some TypeScript files intentionally cover several Python stories:

- `decide/action.mts` covers the main action path.
- `policies/packs.mts` covers the eight packaged policies.
- `policies/group_shadow.mts` covers group and shadow.
- `planners/planners.mts` covers utility, MDP, POMDP and the simulator.
- `learning/causal/causal_planning.mts` covers causal attribution and planning.

Some Python files remain narrative variants rather than separate TypeScript capabilities. The test
suite is the source of truth for behavioural parity.

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

### `decide 1`

- `decide` — the phase restored from the JSON state file.
- `1` — one attributed outcome labelled `helped` was reloaded.

### `act safe_action valve True`

- `act` — the chosen verb.
- `safe_action` — the reason code.
- `valve` — the chosen action.
- `True` — approval is required.

### `executed 3 unknown`

- `executed` — the transient handler succeeded after retries.
- `3` — total attempts.
- `unknown` — the slow async handler timed out; reconcile before retrying.

The full field list is in [`../docs/02-decision/01-contract/01-decision-contract.md`](../docs/02-decision/01-contract/01-decision-contract.md).
The policy contracts are in [`../docs/02-decision/03-decision-shapes/01-single/05-policies.md`](../docs/02-decision/03-decision-shapes/01-single/05-policies.md).
