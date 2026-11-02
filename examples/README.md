# Examples

Each example sends one request to `decide` or `Layer`, or uses one LAIX contract, then prints a short
result. The stories are small everyday situations, so the result is easy to picture.

## Layout

```text
examples/
├── decisions/
│   ├── action/        action selection and custom policy
│   ├── attention/     surfacing, quiet hours, feedback
│   └── records/       decision record, outcome store, parity
├── policies/          packaged policy packs and learned bandit
├── appkit/
│   ├── runtime/       execution, resources, live context, stores
│   ├── audit/         proposal lifecycle
│   ├── platform/      platform interface
│   └── bench/         LAIX-Bench
├── typescript/
│   ├── attention/
│   ├── action/
│   ├── policies/
│   ├── runtime/
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

## Policy packs

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

## Runtime

| File | Piece | Output |
|---|---|---|
| `appkit/runtime/execution.py` | Decision runtime and execution bridge | `executed close the valve` |
| `appkit/runtime/resources.py` | Cheap/deep call admission | `('camera', 'read-page') ('full-audio',)` |
| `appkit/runtime/live_context.py` | Detectors, admission and perception frames | `('motion', 'read-label') ('transcribe',) 2 0.097` |
| `appkit/platform/platform_interface.py` | Run a skill, approve, read events | `7 skill.started,skill.finished fast True` |

## Records

| File | Piece | Output |
|---|---|---|
| `decisions/records/record.py` | Record, approve, execute, verify | `executed True` |
| `appkit/audit/proposal.py` | Proposal lifecycle | `pending approved applied undone` |

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

## Integration

| File | Piece | Output |
|---|---|---|
| `appkit/bench/bench.py` | Run LAIX-Bench from Python | `25 25 1.0` |
| `appkit/runtime/delivery.py` | Delivery port and receipt | `skipped email` |
| `decisions/records/evaluation.py` | Parity harness over cases | `2 2 1.0` |

## TypeScript

| File | Story | Output |
|---|---|---|
| `typescript/attention/bill_due.mts` | The same bill, in TypeScript. | `guide worth_surfacing 84` |
| `typescript/action/action.mts` | The leaking sink, in TypeScript. | `act policy_rule option-close-valve` |
| `typescript/policies/packs.mts` | All eight packaged policy packs. | one line per pack |
| `typescript/policies/bandit.mts` | Outcome learning changes the next choice. | `manual automatic 0.75` |
| `typescript/runtime/live_context.mts` | Cheap and deep detectors under a budget. | `[ 'motion', 'read-label' ] [ 'transcribe' ] 2 0.097` |
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

`packages/python/laix/tests/test_examples.py` runs every example, so none of them can rot.

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

The full field list is in [`../docs/core/01-decisions.md`](../docs/core/01-decisions.md). The policy-pack contracts
are in [`../docs/core/04-policy-packs.md`](../docs/core/04-policy-packs.md).

## Real caller examples

[`apps/`](apps/README.md) contains one example for each of the four working apps. Each app keeps its
own adapter and sends a request to the same `Layer`.
