# Reading a decision

A decision is LAIX’s answer for one bounded task:

- one verb — what the task should do next;
- one reason — why that move;
- optional execution details — the chosen option and intent the app can run.

Everything else on this page explains that answer.

## The terms used here

### The app sends

| Term | Meaning |
|---|---|
| **Request** | What the app sends to LAIX: what is happening and what it can do. |
| **Signal** | One item that might need attention, such as a deadline or a risk. |
| **Context** | Rules around attention: current time, quiet hours, minimum severity. |
| **Option** | One thing the app can do. |

### LAIX returns

| Term | Meaning |
|---|---|
| **Decision** | What LAIX sends back: one verb, a reason, and optional execution details. |
| **Verb** | The word that says what to do next. |
| **Reason code** | A short stable label for the rule that fired. |
| **Chosen option id** (`action_id`) | The id of the chosen option, if there is one. |
| **Confidence** | How sure the rule set is, from `0` to `1`. |
| **Rule-set version** (`policy_version`) | Which version of the rule set produced the decision. |

## Example

A bill is due tomorrow. The app sends a request with one signal and the attention context.

```python
from datetime import datetime, timezone

from laix import Context, DecisionRequest, Signal

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
| `score` | `84.0` | The rule set's ranking. |
| `confidence` | `0.95` | How sure the rule set is. |
| `requires_approval` | `false` | Runs without approval. |
| `deliver` | `true` | Show it now. |
| `record` | `true` | Keep it in history. |

## The decision fields

| Field | Meaning |
|---|---|
| `verb` | What to do next. |
| `confidence` | How sure the rule set is, `0..1`. |
| `reason_code` | The rule that fired. Use this in app logic. |
| `rationale` | Explanation for people. Use `reason_code` in app logic. |
| `action_id` | The chosen option id, if there is one. |
| `intent` | `{capability, args}` the app can execute; for a handover, `Intent("handover", {"target", "reason"})`. |
| `requires_approval` | Ask a person before executing. |
| `reversible` | Whether the chosen option can be undone. |
| `undo_hint` | How to undo it. |
| `score` | Ranking inside one rule set. Use `confidence` for probability. |
| `breakdown` | Score parts for the decision. |
| `cost_of_waiting` | Cost of waiting in this situation. |
| `evidence` | References that support the decision. |
| `decision_id` | Id for records and outcomes. |
| `situation_id` | The id of the situation this decision answered, when there is one. |
| `attributes` | Values the rule set used to reach the decision. |
| `policy_version` | Which version of the rule set produced it. |
| `trace_id` | Correlates related events for this decision. |
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
| `act` | Run the chosen option now. |
| `verify` | Check whether an earlier step worked. |
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

`decision.basis()` returns portable evidence rows:

```python
[
    {"kind": "reason", "ref": "within_risk_limit", "note": "risk is inside the limit"},
    {"kind": "reference", "ref": "sensor-1", "note": "water detected"},
]
```

The app can put these in its own audit record.
