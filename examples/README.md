# Examples

Each example sends one request to `decide` or `Layer`, or uses one LAIX contract, then prints a short
result. The stories are small everyday situations, so the result is easy to picture.

## Layout

```text
examples/
├── decisions/
│   ├── action/        action decisions, engines and custom policy
│   ├── attention/     surfacing, quiet hours, feedback
│   └── records/       DecisionRecord, outcome store, causal, calibration, model learning
├── policies/          packaged policies, authoring, planning, group, shadow, POMDP and learned bandit
├── appkit/
│   ├── runtime/       execution, resources, live context, stores, sagas, simulator, file stores, engine depth
│   ├── streaming/     event time, cadence, backpressure, revisions, windows, checkpoints, sources
│   ├── audit/         proposal lifecycle
│   ├── platform/      platform interface
│   └── bench/         LAIX-Bench
├── typescript/
│   ├── attention/
│   ├── action/
│   ├── policies/
│   ├── runtime/
│   ├── streaming/
│   ├── stores/
│   ├── records/
│   └── integration/
└── apps/              one caller example per working app
```

## Attention

| File | Story | Output |
|---|---|---|
| `decisions/attention/bill_due.py` | An electricity bill is due tomorrow, at 10:00. | `guide worth_surfacing 84.0` |
| `decisions/attention/quiet_hours.py` | The same bill, now at 23:30. | `wait quiet_hours 84.0 True False` |
| `decisions/attention/feedback.py` | The person already dismissed this signal. | `wait dismissed` |

## Action

| File | Story | Output |
|---|---|---|
| `decisions/action/leaking_sink.py` | The kitchen sink is about to overflow. | `act policy_rule option-close-valve` |
| `decisions/action/core_decide.py` | The same sink, answered by core `decide` with no app kit. | `act policy_rule option-close-valve DEC-...` |
| `decisions/action/water_electricity_no_valve.py` | No safe valve: the safety boundary escalates. | `escalate manager 0.7` |
| `decisions/action/pay_bill.py` | A bill is due today and a person must approve the payment. | `act policy_rule option-pay True` |
| `decisions/action/check_again.py` | A parcel is late; a tracking page can settle it. | `observe policy_rule option-check-tracking` |
| `decisions/action/custom_policy.py` | A caller supplies its own policy. | `wait policy_rule` |
| `decisions/action/utility_engine.py` | Expected utility with hard limits. | `act bold 0.75` |
| `decisions/action/mdp_engine.py` | Plan one step in a finite MDP. | `act go 2.8` |

## Packaged policies

| File | Class | Output |
|---|---|---|
| `policies/active_perception.py` | Active perception | `observe observe_for_information look-1` |
| `policies/safety_constrained.py` | Safety-constrained action | `act safe_action valve` |
| `policies/replanning.py` | Replanning | `act replan plan-fast` |
| `policies/allocation.py` | Allocation | `act allocate ['a', 'b']` |
| `policies/negotiation.py` | Negotiation | `act counter_offer 12.5` |
| `policies/preference_elicitation.py` | Preference elicitation | `ask ask_preference q2` |
| `policies/verification.py` | Verification | `verify verify_outcome api` |
| `policies/escalation.py` | Escalation | `escalate escalate_to_target manager` |
| `policies/bandit.py` | Outcome learning | `manual automatic 0.75` |
| `policies/time_critical.py` | Gates, delay, cost, disruption and confidence | `act breaker-dry 0.44` |
| `policies/authoring.py` | Rule policy with a target and recipients | `ask over_limit some ('alice', 'ben')` |
| `policies/planning.py` | Commitment-based next move | `act due_commitment a` |
| `policies/planning_store.py` | Persist and restore a commitment ledger | `send the draft` |
| `policies/group.py` | Target, recipients and private masking | `all ('alice', 'ben', 'chris') {'topic': 'math'}` |
| `policies/shadow.py` | Shadow policy records a disagreement | `ask 1 act` |
| `policies/pomdp.py` | Belief update and finite-horizon planning | `act go 2.8` |

## Runtime

| File | Piece | Output |
|---|---|---|
| `appkit/runtime/execution.py` | Decision runtime and execution bridge | `executed close the valve` |
| `appkit/runtime/resources.py` | Cheap/deep call admission | `('camera', 'read-page') ('full-audio',)` |
| `appkit/runtime/live_context.py` | Detectors, admission and perception frames | `('motion', 'read-label') ('transcribe',) 2 0.097` |
| `appkit/runtime/saga.py` | Forward steps and reverse compensation | `('first',) ('first',) RuntimeError: boom` |
| `appkit/runtime/execution_saga.py` | Bridge execution with receipt-linked compensation | `('reserve',) ('reserve',) RuntimeError: declined` |
| `appkit/runtime/simulator.py` | Compare engines on one scenario | `right 4.0 1.0` |
| `appkit/runtime/file_stores.py` | Persist a checkpoint and a commitment ledger | `1 send the draft` |
| `appkit/runtime/engine_depth.py` | Constraints, stochastic simulation and POMDP comparison | `safe blocked by risk:risk-limit` / `s1 1.0` / `s0 0.0 go` |
| `appkit/platform/platform_interface.py` | Run a skill, approve, read events | `7 skill.started,skill.finished fast True` |

## Records

| File | Piece | Output |
|---|---|---|
| `decisions/records/record.py` | Record, approve, execute, verify | `executed True` |
| `appkit/audit/proposal.py` | Proposal lifecycle | `pending approved applied undone` |
| `decisions/records/causal.py` | Estimate a treatment effect | `1.0 difference-in-means` |
| `decisions/records/causal_outcomes.py` | Build a causal ledger from outcomes | `6.0 6.0 6.0` |
| `decisions/records/causal_strata.py` | Causal intervals and strata | `1.0 -1.771859 3.771859 ['east', 'west']` |
| `decisions/records/calibration.py` | Compare confidence with accuracy | `0.9 0.5 0.4 0.5` |
| `decisions/records/model_learning.py` | Learn transitions and reward | `{'s1': 1.0} 2.0` |

## Stores

| File | Piece | Output |
|---|---|---|
| `appkit/runtime/state_store.py` | Save, load and delete an experience snapshot | `decide True` |
| `decisions/records/outcome_store.py` | Record what a decision changed | `helped -2.0 1` |

## Host integration

| File | Shows | Output |
|---|---|---|
| `appkit/runtime/mission_adapter.py` | Task → request → decision → basis | `act valve host-calibrated True reason` |
| `appkit/runtime/mission_execution.py` | Approval → execution → receipt | `executed approve the repair True` |
| `appkit/streaming/stream_session.py` | One event → a decision stream → close | `guide worth_surfacing STR-DEMO final` |
| `appkit/streaming/checkpoint.py` | Save and resume a stream | `True 1 1` |
| `appkit/streaming/sources.py` | Read NDJSON into requests | `a b` |
| `appkit/streaming/dead_letter.py` | Retain a malformed frame and continue | `a b 1 True` |
| `appkit/streaming/windows.py` | Aggregate events into tumbling windows | `['2 events', '1 events']` |
| `appkit/streaming/flow_control.py` | Cooldown, budget and replay | `1 0 0 1 1 ['d', 'e']` |

## Integration

| File | Piece | Output |
|---|---|---|
| `appkit/bench/bench.py` | Run LAIX-Bench from Python | `25 25 1.0` |
| `appkit/bench/engine_bench.py` | Compare the MDP planner with a baseline | `mdp 4.0 1.0` |
| `appkit/runtime/delivery.py` | Delivery port and receipt | `skipped email` |
| `decisions/records/evaluation.py` | Parity harness over cases | `2 2 1.0` |

## TypeScript

| File | Story | Output |
|---|---|---|
| `typescript/attention/bill_due.mts` | The same bill, in TypeScript. | `guide worth_surfacing 84` |
| `typescript/action/action.mts` | The leaking sink, in TypeScript. | `act policy_rule option-close-valve` |
| `typescript/policies/packs.mts` | All eight packaged policies. | one line per policy |
| `typescript/policies/bandit.mts` | Outcome learning changes the next choice. | `manual automatic 0.75` |
| `typescript/runtime/live_context.mts` | Cheap and deep detectors under a budget. | `[ 'motion', 'read-label' ] [ 'transcribe' ] 2 0.097` |
| `typescript/streaming/stream_session.mts` | One event → a decision stream → close. | `guide worth_surfacing STR-DEMO final` |
| `typescript/runtime/execution.mts` | Decide, execute, record a receipt. | `executed close the valve` |
| `typescript/runtime/platform.mts` | Run a skill, approve, read events. | `7 skill.started,skill.finished fast true` |
| `typescript/runtime/resources.mts` | Cheap/deep admission. | `[ 'camera', 'read-page' ] [ 'full-audio' ]` |
| `typescript/stores/state_store.mts` | Save, load and delete experience state. | `decide true` |
| `typescript/stores/outcome_store.mts` | Record a measured outcome. | `helped -2 1` |
| `typescript/records/proposal.mts` | Proposal lifecycle. | `pending approved applied undone` |
| `typescript/records/record.mts` | Decision record lifecycle. | `executed true` |
| `typescript/integration/bench.mts` | Run LAIX-Bench from TypeScript. | `25 25 1` |
| `typescript/integration/delivery.mts` | Delivery port and receipt. | `skipped email` |
| `typescript/integration/evaluation.mts` | Parity harness. | `2 2 1` |
| `typescript/streaming/checkpoint.mts` | Checkpoint, resume and NDJSON source. | `true 1 a b` |
| `typescript/policies/causal_planning.mts` | Causal effect and commitment planning. | `1 difference-in-means act a` |
| `typescript/policies/group_shadow.mts` | Group masking and shadow comparison. | `ask act all {"topic":"math"}` |
| `typescript/runtime/saga.mts` | Forward steps and reverse compensation. | `first first Error: boom` |
| `typescript/integration/engines.mts` | Utility, MDP, simulator and comparison. | `bold 0.75 go 2.8 right 0` |
| `typescript/integration/engine_bench.mts` | Engine bench baseline comparison. | `mdp 4 1` |
| `typescript/records/calibration.mts` | Confidence vs accuracy. | `0.9 0.5 0.4 0.5` |
| `typescript/records/model_learning.mts` | Learn transitions and reward. | `{"s1":1} 2` |
| `typescript/policies/pomdp.mts` | Belief planning. | `act go 2.8` |
| `typescript/policies/planning_store.mts` | Persist a commitment ledger. | `send the draft` |
| `typescript/streaming/dead_letter.mts` | Retain a malformed frame. | `a b 1 true` |
| `typescript/runtime/execution_saga.mts` | Bridge execution with compensation. | `reserve reserve Error: declined` |
| `typescript/policies/authoring.mts` | Rule policy with a target. | `ask over_limit some alice,ben` |
| `typescript/streaming/windows.mts` | Tumbling windows. | `[ '2 events', '1 events' ]` |
| `typescript/streaming/flow_control.mts` | Cooldown, budget and replay. | `1 0 0 1 1 [ 'd', 'e' ]` |
| `typescript/records/causal_strata.mts` | Causal intervals and strata. | `1 -1.771859 3.771859 [ 'east', 'west' ]` |
| `typescript/runtime/file_stores.mts` | File-backed checkpoint and commitment stores. | `1 send the draft` |

## Run

From the repository root:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
Get-ChildItem examples/decisions, examples/policies, examples/appkit -Recurse -Filter *.py | ForEach-Object { py $_.FullName }
Get-ChildItem examples/apps/*.py | ForEach-Object { py $_.FullName }
```

A single example:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/policies/active_perception.py
```

The TypeScript examples run with Node's type stripping:

```powershell
Get-ChildItem examples/typescript -Recurse -Filter *.mts | ForEach-Object { node --experimental-strip-types $_.FullName }
```

`packages/python/laix/tests/test_examples.py` runs every Python example, and CI runs every
TypeScript example, so none of them can rot.

## What the output means

### `guide worth_surfacing 84.0`

- `guide` — show the bill to the user now. The user decides when to pay.
- `worth_surfacing` — the rule that says the bill is worth surfacing.
- `84.0` — the policy score. A higher score means the item is more worth showing.

### `wait quiet_hours 84.0 True False`

- `wait` — stay silent now.
- `quiet_hours` — quiet hours are active, so the bill waits.
- `84.0` — the score still says it is important.
- `True` — keep it on record for the morning digest.
- `False` — hold it for later.

### `act policy_rule option-close-valve`

- `act` — do something now.
- `policy_rule` — a written policy rule made the choice.
- `option-close-valve` — the chosen action is to close the valve.

### `act policy_rule option-pay True`

- `act` — the policy chooses to pay now.
- `policy_rule` — a written policy rule made the choice.
- `option-pay` — the chosen action is the payment.
- `True` — a person must approve before the payment runs.

### `observe policy_rule option-check-tracking`

- `observe` — get more information yourself before deciding.
- `policy_rule` — a written policy rule made the choice.
- `option-check-tracking` — the chosen action is to read the tracking page.

### `executed True`

- `executed` — the record moved from approved to executed.
- `True` — the record fingerprint still matches its content.

The full field list is in [`../docs/core/01-decision-contract.md`](../docs/core/01-decision-contract.md). The policy-pack contracts
are in [`../docs/core/03-packaged-policies.md`](../docs/core/03-packaged-policies.md).

## Real caller examples

[`apps/`](apps/README.md) contains one example for each of the four working apps. Each app keeps its
own adapter and sends a request to the same `Layer`.
