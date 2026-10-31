# What a decision means

A request goes in. One decision comes out. This page explains the words in that decision in plain
language.

## A simple request

An electricity bill is due tomorrow. The app asks LAIX whether to show it now.

| Field | Meaning in this story |
|---|---|
| `subject` | "electricity bill" — a name for the decision, used in logs. |
| `at` | 10:00 on 1 November — the time of the request. |
| `signals` | one item: "Electricity bill due tomorrow". |
| `severity` | `high` — the bill matters. |
| `confidence` | 0.95 — the app is 95% sure the bill is real. |
| `due` | 09:00 on 2 November — the deadline is within 24 hours. |
| `context.now` | 10:00 — quiet hours are 22:00 to 06:00, so this is daytime. |
| `context.min_severity` | `medium` — ignore items below medium. |

## The result

```text
guide worth_surfacing 84.0
```

| Field | Meaning in this story |
|---|---|
| `verb` | `guide` — show the bill to the user now. The user decides when to pay. |
| `reason_code` | `guide` — the rule that says the bill is worth surfacing. |
| `score` | 84.0 — the policy's ranking number. A higher score means more worth showing. |
| `confidence` | 0.95 — how sure the layer is. |
| `requires_approval` | false — showing the bill runs directly. |
| `deliver` | true — show it now. |
| `record` | true — keep it in the history. |

## The same bill at 23:30

```text
wait quiet_hours 84.0 True False
```

| Field | Meaning |
|---|---|
| `verb` | `wait` — stay silent now. |
| `reason_code` | `quiet_hours` — quiet hours are active. |
| `score` | 84.0 — the bill is still important. |
| `record` | true — keep it for the morning digest. |
| `deliver` | false — hold it for later. |

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

## Getting more information

A parcel is late. A tracking page can settle it.

```text
observe policy_rule option-check-tracking
```

| Field | Meaning in this story |
|---|---|
| `verb` | `observe` — get more information yourself before deciding. |
| `reason_code` | `policy_rule` — a written policy rule made the choice. |
| `action_id` | `option-check-tracking` — read the tracking page. |

The rule chooses this cheap check before asking the courier.

## A chosen action

An overflowing sink is urgent. The app offers two options: watch it, or close the valve.

```text
act policy_rule option-close-valve
```

| Field | Meaning in this story |
|---|---|
| `verb` | `act` — do something now. |
| `reason_code` | `policy_rule` — a written policy rule made the choice. |
| `action_id` | `option-close-valve` — the chosen action is to close the valve. |
| `score` | the chosen option's utility: benefit minus a share of risk and interruption cost. |

## A payment that needs approval

A bill is due today. The payment is an action that a person must approve.

```text
act policy_rule option-pay True
```

| Field | Meaning in this story |
|---|---|
| `verb` | `act` — the policy chooses to pay now. |
| `action_id` | `option-pay` — the chosen action is the payment. |
| `requires_approval` | true — a person must approve before the payment runs. |

The layer makes the choice. The app asks for approval and runs the payment after approval.

## A record

```text
executed True
```

| Field | Meaning |
|---|---|
| `executed` | the record moved from approved to executed. |
| `True` | the record fingerprint still matches its content. |

The record moves through these states:

```text
draft -> approved -> executed -> undone
  |
  +-> rejected
```
