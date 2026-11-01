# What is LAIX?

LAIX helps a product answer one question:

> Given this situation, what should happen next?

It returns one of seven answers:

```text
wait    observe    guide    ask    act    verify    escalate
```

Then the product does the work.

## A simple example

Water is coming under the bathroom door.

- LAIX sees: a leak, high urgency, a valve it is allowed to close.
- LAIX returns: **act — close the valve**.
- The product closes the valve.
- Later, LAIX can choose **verify — check that the water stopped**.

## What LAIX does not do

LAIX does not:

- remember the user's apps or history;
- connect to mail, calendars or sensors;
- decide when to interrupt the user;
- own permissions or approvals;
- run missions or dispatch agents;
- execute the action.

The product owns all of that. LAIX owns the one decision and its record.

## How it fits

```text
product decides a task exists
        │
        ▼
task asks LAIX for one decision
        │
        ▼
LAIX returns one decision
        │
        ▼
product acts, asks, waits or escalates
```

LAIX is a **tool inside a task**, not a second product manager.

## What the decision carries

- what to do;
- why;
- how sure it is and where that confidence came from;
- whether a person must approve;
- what to record.

The product keeps its memory, permissions and user relationship.

## Read next

- [Architecture](architecture.md) — the full picture.
- [Host integration](host-integration.md) — the six things a host team checks first.
- [Reading a decision](core/decisions.md) — every field in plain language.
