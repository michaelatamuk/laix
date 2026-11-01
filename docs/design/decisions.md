# Reading a decision

One request goes in. One decision comes out. This page explains every field in plain language.

## A worked example

An electricity bill is due tomorrow. The app asks LAIX whether to show it now.

```python
DecisionRequest(
    subject="electricity bill",
    at="2026-11-01T10:00:00+00:00",
    signals=(Signal(
        id="bill-1",
        kind="deadline",
        title="Electricity bill due tomorrow",
        severity="high",
        confidence=0.95,
        due="2026-11-02T09:00:00+00:00",
    ),),
    context=Context(
        now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        quiet_hours=("22:00", "06:00"),
        min_severity="medium",
    ),
)
```

The decision is:

```text
guide worth_surfacing 84.0
```

| Field | Value | Meaning |
|---|---|---|
| `verb` | `guide` | Show the bill to the user now; the user decides when to pay. |
| `reason_code` | `worth_surfacing` | The signal cleared the attention rules. |
| `score` | `84.0` | The attention policy's ranking number; higher means more worth showing. |
| `confidence` | `0.95` | How sure the layer is. |
| `requires_approval` | `false` | Showing the bill does not need approval. |
| `deliver` | `true` | Send it now. |
| `record` | `true` | Keep it in the history. |

## Field reference

### The outcome

| Field | Type | Meaning |
|---|---|---|
| `verb` | one of seven | What to do next. |
| `confidence` | `0..1` | How sure the policy is. |
| `reason_code` | string | The rule that fired. Stable enough to branch on. |
| `rationale` | string | A human-readable explanation. |

### The choice

| Field | Type | Meaning |
|---|---|---|
| `action_id` | string or `null` | The chosen option, when there is one. |
| `intent` | object or `null` | `{capability, args}` the app can execute. |
| `requires_approval` | boolean | A person must approve before execution. |
| `reversible` | boolean | Whether the action can be undone. |
| `undo_hint` | string or `null` | How the app should undo it. |

### The cost

| Field | Type | Meaning |
|---|---|---|
| `score` | number or `null` | The policy's ranking score. It is not a probability. |
| `breakdown` | object or `null` | Named score components for attention decisions. |
| `cost_of_waiting` | number | How much waiting costs in this situation. |

### The evidence

| Field | Type | Meaning |
|---|---|---|
| `evidence` | list | References with `id`, `kind`, `quote`, `source`, `confidence`. |
| `escalation` | object or `null` | `{target, reason}` when the decision is to escalate. |

### The audit trail

| Field | Type | Meaning |
|---|---|---|
| `decision_id` | string | The id to use in records and outcomes. |
| `policy_version` | string | Which policy produced the decision. |
| `trace_id` | string | Correlates the decision with execution and platform events. |
| `deliver` | boolean | Whether the app should surface it now. |
| `record` | boolean | Whether the app should keep it. |
| `created_at` | timestamp | When the decision was made. |

## The seven verbs

| Verb | Plain meaning |
|---|---|
| `wait` | Do nothing now. Keep watching. |
| `observe` | Get more information yourself: take another look, fetch a reading, run a cheap check. |
| `guide` | Show the user what is happening. Let the user choose. |
| `ask` | Ask a person or another agent for information or a decision. |
| `act` | Run the chosen action now. |
| `verify` | Check whether an earlier action worked. |
| `escalate` | Hand the decision to a person with more authority. |

`notify` is a delivery action, not a decision verb. When an app notifies someone, the decision is
`guide` and the app chooses the channel. Approval is a flag on the decision.

## More examples

### Quiet hours

The same bill at 23:30:

```text
wait quiet_hours 84.0 True False
```

| Field | Meaning |
|---|---|
| `verb` | `wait` — stay silent now. |
| `reason_code` | `quiet_hours` — quiet hours are active. |
| `score` | `84.0` — the bill is still important. |
| `record` | `true` — keep it for the morning digest. |
| `deliver` | `false` — hold it for later. |

### Look before deciding

A parcel is late and a tracking page can settle it:

```text
observe policy_rule option-check-tracking
```

`action_id` is `option-check-tracking`. The policy prefers a cheap check before asking the courier.

### Act now

An overflowing sink is urgent:

```text
act policy_rule option-close-valve
```

`action_id` is `option-close-valve`. The `score` is the chosen option's utility: benefit minus a
share of risk and interruption cost.

### Act with approval

A bill is due today and payment needs a person:

```text
act policy_rule option-pay True
```

`requires_approval` is `true`. The layer chooses to pay; the app asks for approval and only then
executes.

## Score, reason code and version

- **`score`** ranks options inside one policy. Do not compare scores across different policies.
- **`reason_code`** tells you why this rule fired. It is the stable field for app logic.
- **`rationale`** is for people and logs; do not parse it.
- **`policy_version`** tells you which policy produced the decision. A policy change can change a
  score without changing the contract.

## A decision record

```text
executed True
```

`executed` means the record moved from approved to executed. `True` means its fingerprint still
matches its content.

```text
draft -> approved -> executed -> undone
  |
  +-> rejected
```

## Where to go next

- Field names come from the versioned [contracts](contracts.md).
- The two common policies are attention and action; the other eight are in
  [policy packs](../guides/policy-packs.md).
- Executing a decision is covered in [integration](../guides/integration.md) and
  [architecture](architecture.md).
