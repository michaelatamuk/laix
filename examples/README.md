# Examples

Each example sends one request to `Layer` or uses one LAIX contract, then prints a short result. The
stories are small everyday situations, so the result is easy to picture.

## Common decisions

| File | Story | Output |
|---|---|---|
| `python/bill_due.py` | An electricity bill is due tomorrow, at 10:00. | `guide worth_surfacing 84.0` |
| `python/quiet_hours.py` | The same bill, now at 23:30. | `wait quiet_hours 84.0 True False` |
| `python/leaking_sink.py` | The kitchen sink is about to overflow. | `act policy_rule option-close-valve` |
| `python/pay_bill.py` | A bill is due today and a person must approve the payment. | `act policy_rule option-pay True` |
| `python/check_again.py` | A parcel is late; a tracking page can settle it. | `observe policy_rule option-check-tracking` |
| `python/custom_policy.py` | A caller supplies its own policy. | `wait policy_rule` |
| `python/record.py` | Record the payment, approve it, execute it. | `executed True` |
| `python/feedback.py` | The person already dismissed this signal. | `wait dismissed` |

## Policy packs

| File | Class | Output |
|---|---|---|
| `python/active_perception.py` | Active perception | `observe observe_for_information look-1` |
| `python/safety.py` | Safety-constrained action | `act safe_action valve` |
| `python/replanning.py` | Replanning | `act replan plan-fast` |
| `python/allocation.py` | Allocation | `act allocate ['a', 'b']` |
| `python/negotiation.py` | Negotiation | `act counter_offer 12.5` |
| `python/preference.py` | Preference elicitation | `ask ask_preference q2` |

## Platform and contracts

| File | Piece | Output |
|---|---|---|
| `python/platform_interface.py` | Run a skill, approve, read events | `7 skill.started,skill.finished fast True` |
| `python/state_store.py` | Save, load and delete an experience snapshot | `decide True` |
| `python/outcome_store.py` | Record what a decision changed | `helped -2.0 1` |
| `python/proposal.py` | Proposal lifecycle | `pending approved applied undone` |
| `python/delivery.py` | Delivery port and receipt | `skipped email` |
| `python/evaluation.py` | Parity harness over cases | `2 2 1.0` |
| `python/resources.py` | Cheap/deep call admission | `('camera', 'read-page') ('full-audio',)` |
| `python/execution.py` | Decision runtime and execution bridge | `executed close the valve` |

## Run

From the repository root:

```powershell
$env:PYTHONPATH = "python/laix/src"
Get-ChildItem examples/python/*.py | ForEach-Object { py $_.FullName }
Get-ChildItem examples/apps/*.py | ForEach-Object { py $_.FullName }
```

A single example:

```powershell
$env:PYTHONPATH = "python/laix/src"
py examples/python/active_perception.py
```

The TypeScript example runs with Node's type stripping:

```powershell
node --experimental-strip-types examples/typescript/bill_due.mts
```

`python/laix/tests/test_examples.py` runs every example, so none of them can rot.

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

The full field list is in [`../docs/decisions.md`](../docs/decisions.md). The policy-pack contracts
are in [`../docs/policy-packs.md`](../docs/policy-packs.md).

## Real caller examples

[`apps/`](apps/README.md) contains one example for each of the four working apps. Each app keeps its
own adapter and sends a request to the same `Layer`.
