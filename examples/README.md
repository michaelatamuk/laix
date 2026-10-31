# Examples

Each example sends one request to `Layer` and prints the decision. The stories are small everyday
situations, so the result is easy to picture.

| File | Story | Output |
|---|---|---|
| `python/bill_due.py` | An electricity bill is due tomorrow, at 10:00. | `guide worth_surfacing 84.0` |
| `python/quiet_hours.py` | The same bill, now at 23:30. | `wait quiet_hours 84.0 True False` |
| `python/leaking_sink.py` | The kitchen sink is about to overflow. | `act policy_rule option-close-valve` |
| `python/pay_bill.py` | A bill is due today and a person must approve the payment. | `act policy_rule option-pay True` |
| `python/check_again.py` | A parcel is late; a tracking page can settle it. | `observe policy_rule option-check-tracking` |
| `python/custom_policy.py` | A caller supplies its own policy. | `wait policy_rule` |
| `python/record.py` | Record the payment, approve it, execute it. | `executed True` |
| `typescript/bill_due.mts` | The same bill, in TypeScript. | `guide worth_surfacing 84` |

Run from the repository root:

```powershell
$env:PYTHONPATH = "python/laix/src"
py examples/python/bill_due.py
py examples/python/quiet_hours.py
py examples/python/leaking_sink.py
py examples/python/pay_bill.py
py examples/python/check_again.py
py examples/python/custom_policy.py
py examples/python/record.py
```

The TypeScript example runs with Node's type stripping:

```powershell
node --experimental-strip-types examples/typescript/bill_due.mts
```

## What the output means

### `guide worth_surfacing 84.0`

- `guide` — show the bill to the user now. The user decides when to pay.
- `guide` — the reason is the rule that says the bill is worth surfacing.
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

The full field list is in [`../docs/decisions.md`](../docs/decisions.md).

## Real caller examples

[`apps/`](apps/README.md) contains one example for each of the four working apps. Each app keeps its
own adapter and sends a request to the same `Layer`.
