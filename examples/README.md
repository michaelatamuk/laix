# Examples

Each example sends one request to `Layer` or uses one LAIX contract, then prints a short result. The
stories are small everyday situations, so the result is easy to picture.

## Layout

```text
examples/
├── python/
│   ├── attention/     surfacing, quiet hours, feedback
│   ├── action/        action selection and custom policy
│   ├── policies/      reference policy packs and learned bandit
│   ├── runtime/       execution, resources, platform
│   ├── records/       decision record and proposal
│   ├── stores/        state store and outcome store
│   └── integration/   delivery and evaluation
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
| `python/attention/bill_due.py` | An electricity bill is due tomorrow, at 10:00. | `guide worth_surfacing 84.0` |
| `python/attention/quiet_hours.py` | The same bill, now at 23:30. | `wait quiet_hours 84.0 True False` |
| `python/attention/feedback.py` | The person already dismissed this signal. | `wait dismissed` |

## Action

| File | Story | Output |
|---|---|---|
| `python/action/leaking_sink.py` | The kitchen sink is about to overflow. | `act policy_rule option-close-valve` |
| `python/action/pay_bill.py` | A bill is due today and a person must approve the payment. | `act policy_rule option-pay True` |
| `python/action/check_again.py` | A parcel is late; a tracking page can settle it. | `observe policy_rule option-check-tracking` |
| `python/action/custom_policy.py` | A caller supplies its own policy. | `wait policy_rule` |

## Policy packs

| File | Class | Output |
|---|---|---|
| `python/policies/active_perception.py` | Active perception | `observe observe_for_information look-1` |
| `python/policies/safety.py` | Safety-constrained action | `act safe_action valve` |
| `python/policies/replanning.py` | Replanning | `act replan plan-fast` |
| `python/policies/allocation.py` | Allocation | `act allocate ['a', 'b']` |
| `python/policies/negotiation.py` | Negotiation | `act counter_offer 12.5` |
| `python/policies/preference.py` | Preference elicitation | `ask ask_preference q2` |
| `python/policies/verification.py` | Verification | `verify verify_outcome api` |
| `python/policies/escalation.py` | Escalation | `escalate escalate_to_target manager` |
| `python/policies/bandit.py` | Outcome learning | `manual automatic 0.75` |

## Runtime

| File | Piece | Output |
|---|---|---|
| `python/runtime/execution.py` | Decision runtime and execution bridge | `executed close the valve` |
| `python/runtime/resources.py` | Cheap/deep call admission | `('camera', 'read-page') ('full-audio',)` |
| `python/runtime/live_context.py` | Detectors, admission and perception frames | `('motion', 'read-label') ('transcribe',) 2 0.097` |
| `python/runtime/platform_interface.py` | Run a skill, approve, read events | `7 skill.started,skill.finished fast True` |

## Records

| File | Piece | Output |
|---|---|---|
| `python/records/record.py` | Record, approve, execute, verify | `executed True` |
| `python/records/proposal.py` | Proposal lifecycle | `pending approved applied undone` |

## Stores

| File | Piece | Output |
|---|---|---|
| `python/stores/state_store.py` | Save, load and delete an experience snapshot | `decide True` |
| `python/stores/outcome_store.py` | Record what a decision changed | `helped -2.0 1` |

## Integration

| File | Piece | Output |
|---|---|---|
| `python/integration/bench.py` | Run LAIX-Bench from Python | `25 25 1.0` |
| `python/integration/delivery.py` | Delivery port and receipt | `skipped email` |
| `python/integration/evaluation.py` | Parity harness over cases | `2 2 1.0` |

## TypeScript

| File | Story | Output |
|---|---|---|
| `typescript/attention/bill_due.mts` | The same bill, in TypeScript. | `guide worth_surfacing 84` |
| `typescript/action/action.mts` | The leaking sink, in TypeScript. | `act policy_rule option-close-valve` |
| `typescript/policies/packs.mts` | All eight reference policy packs. | one line per pack |
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
Get-ChildItem examples/python -Recurse -Filter *.py | ForEach-Object { py $_.FullName }
Get-ChildItem examples/apps/*.py | ForEach-Object { py $_.FullName }
```

A single example:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/python/policies/active_perception.py
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

The full field list is in [`../docs/design/decisions.md`](../docs/design/decisions.md). The policy-pack contracts
are in [`../docs/guides/policy-packs.md`](../docs/guides/policy-packs.md).

## Real caller examples

[`apps/`](apps/README.md) contains one example for each of the four working apps. Each app keeps its
own adapter and sends a request to the same `Layer`.
