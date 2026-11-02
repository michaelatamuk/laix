# Reading a decision

## First, the words

| Word | Meaning |
|---|---|
| **Request** | What the app sends to LAIX: what is happening and what it can do. |
| **Signal** | One item that might need attention, such as a deadline or a risk. |
| **Context** | Rules around attention: current time, quiet hours, minimum severity. |
| **Situation** | The current state for an action decision: beliefs, goals and limits. |
| **Option** | One action the app can take. |
| **Decision** | What LAIX sends back: one verb, a reason, and optional action details. |
| **Verb** | The action word in a decision. |
| **Policy** | The rule set that produced the decision. |
| **Reason code** | A short stable label for the rule that fired. |

## Example

A bill is due tomorrow. The app sends a request with one signal and the attention context.

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

LAIX returns:

```text
guide worth_surfacing 84.0
```

| Field | Value | Meaning |
|---|---|---|
| `verb` | `guide` | Show the bill now; the user decides when to pay. |
| `reason_code` | `worth_surfacing` | The attention rules say it is worth showing. |
| `score` | `84.0` | The attention policy's ranking. |
| `confidence` | `0.95` | How sure LAIX is. |
| `requires_approval` | `false` | Runs without approval. |
| `deliver` | `true` | Show it now. |
| `record` | `true` | Keep it in history. |

## The decision fields

| Field | Meaning |
|---|---|
| `verb` | What to do next. |
| `confidence` | How sure the policy is, `0..1`. |
| `reason_code` | The rule that fired. Use this in app logic. |
| `rationale` | Explanation for people. Use `reason_code` in app logic. |
| `action_id` | The chosen option, if there is one. |
| `intent` | `{capability, args}` the app can execute. |
| `requires_approval` | Ask a person before executing. |
| `reversible` | Whether the action can be undone. |
| `undo_hint` | How to undo it. |
| `score` | Ranking inside one policy. Use `confidence` for probability. |
| `breakdown` | Score parts for attention decisions. |
| `cost_of_waiting` | Cost of waiting in this situation. |
| `evidence` | References that support the decision. |
| `escalation` | `{target, reason}` when handing over. |
| `decision_id` | Id for records and outcomes. |
| `situation_id` | The situation this decision answered, when there is one. |
| `attributes` | Policy-specific values used to reach the decision. |
| `policy_version` | Which policy produced it. |
| `trace_id` | Correlates execution and platform events. |
| `deliver` | Show now. |
| `record` | Keep it. |
| `created_at` | When it was made. |
| `confidence_source` | Where the confidence came from. |
| `calibrated` | Whether the confidence is a calibrated probability. |
| `alternatives` | Other options, their score and why they lost. |
| `constraints_applied` | Hard limits that changed the option set. |

## The seven verbs

| Verb | Meaning |
|---|---|
| `wait` | Hold for now; keep watching. |
| `observe` | Get more information first. |
| `guide` | Show the situation to a person. |
| `ask` | Ask a person or agent for information or a decision. |
| `act` | Run the chosen action now. |
| `verify` | Check whether an earlier action worked. |
| `escalate` | Hand over to someone with more authority. |

A notification is a `guide` decision plus an app delivery channel. Approval is the
`requires_approval` flag.

## More examples

**Quiet hours.** The same bill at 23:30 returns `wait quiet_hours 84.0`. The score is still high, but
`deliver` is `false` and `record` is `true`.

**Look first.** A late parcel with a tracking page returns `observe policy_rule option-check-tracking`.

**Act.** An overflowing sink returns `act policy_rule option-close-valve`.

**Approval.** A payment returns `act policy_rule option-pay` with `requires_approval = true`.

## Decision basis

`decision.basis()` returns host-neutral evidence rows:

```python
[
    {"kind": "reason", "ref": "safe_action", "note": "risk is inside the limit"},
    {"kind": "reference", "ref": "sensor-1", "note": "water detected"},
]
```

The host can put these in its own audit record.

## Records

A decision record moves through:

```text
draft -> approved -> executed -> undone
  |
  +-> rejected
```

`executed True` means the record ran and its fingerprint still matches.

## Next

- [Contracts](contracts.md) explains the version and record shapes.
- [Policy packs](policy-packs.md) covers the other eight decision classes.
- [Integration](../appkit/integration.md) shows how to execute a decision.
