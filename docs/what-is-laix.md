# What is LAIX?

LAIX helps a product answer one question:

> Given this situation, what should happen next?

It returns one of seven answers:

```text
wait    observe    guide    ask    act    verify    escalate
```

Then the product does the work.

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

LAIX is a **tool inside a task**. The product keeps its own orchestration.

## A simple example

Water is coming under the bathroom door.

- LAIX sees: a leak, high urgency, a valve it is allowed to close.
- LAIX returns: **act — close the valve**.
- The product closes the valve.
- Later, LAIX can choose **verify — check that the water stopped**.

## What a decision carries

- what to do;
- why;
- how sure it is and where that confidence came from;
- whether a person must approve;
- what to record.

## A harder example: water and electricity

Water is under the bathroom door and has reached a socket. The water valve is out of reach. A dry
service corridor reaches the main breaker in 4 minutes. In about 6 minutes the water may reach the
consumer unit, so the next option has to fit inside that window.

What LAIX sees:

- a leak, with high urgency;
- electricity near water, with high risk;
- the socket is probably live — confidence **0.80**;
- a hard rule: risk must stay at or below **0.20**;
- a 6-minute window before the damage gets worse;
- options with different risk, delay, money cost, disruption and information value.

### First the gates, then the score

Two hard gates run before any score:

1. **Risk above 0.20** leaves the set. Crossing the wet floor is out.
2. **Delay above 6 minutes** leaves the set. A safe option that arrives too late is not the next
   option. It can still be the follow-up.

The remaining options are scored:

```text
score = confidence × benefit
      − 0.25 × risk
      − 0.05 × delay_minutes
      − 0.002 × cost
      − 0.15 × disruption
      + 0.20 × information_gain × (1 − confidence)
```

Each term has a meaning:

- **confidence × benefit** — the benefit only counts if the socket is really live;
- **risk** — personal injury, not property damage;
- **delay** — time lost inside a 6-minute window;
- **cost** — money, such as a callout fee;
- **disruption** — alarms, power off, people moved;
- **information gain** — looking first is worth more when confidence is low.

| Option | Benefit | Risk | Delay | Cost | Disruption | Score |
|---|---|---|---|---|---|---|
| Cross the wet floor | 1.00 | 0.90 | 0 min | 0 | 0 | gate: risk |
| Dry corridor to the breaker | 0.85 | 0.10 | 4 min | 0 | 0.10 | **0.4400** |
| Call an electrician | 0.70 | 0.00 | 15 min | 120 | 0.05 | gate: too late |
| Evacuate and raise the alarm | 0.60 | 0.03 | 1 min | 0 | 0.50 | 0.3475 |
| Look from the doorway | 0.50 | 0.05 | 2 min | 0 | 0 | 0.3275 |
| Wait | 0.10 | 0.00 | 0 min | 0 | 0 | 0.0800 |

The decision is:

- **act** — use the dry corridor to the breaker;
- **score** — 0.4400;
- **verify** — check that the socket is dead;
- **follow-up** — call an electrician to check the socket and the consumer unit.

The wet route is removed because risk 0.90 is above the hard limit. The electrician is safe and
cheap in risk, but 15 minutes is outside the window, so it cannot be the next option. Evacuation is
fast and safe, but it does not stop the water and it disrupts the building. Looking is cheap, but at
confidence 0.80 it delays a known problem.

### When confidence changes, the answer changes

Set confidence to **0.45**: the socket may be dead, and the benefit of cutting power is less certain.
The same gates apply, but the scores change:

| Option | Score |
|---|---|
| Look from the doorway | **0.2225** |
| Dry corridor to the breaker | 0.1425 |
| Evacuate and raise the alarm | 0.1375 |
| Wait | 0.0450 |

Now the decision is:

- **observe** — look from the doorway;
- **then** — re-decide with better information.

A 2-minute look is cheaper than a 4-minute trip to cut power for a socket that may not be live.
That is the point of the information term: when confidence is low, buying information can beat
acting.

If the dry corridor is blocked, evacuation wins with **0.3475**. The electrician stays the follow-up
in every branch.

This example uses a small policy plugin. The built-in action policy ranks benefit, risk and
interruption cost. An app that needs money, delay, disruption and information value adds those
terms in its own policy.

Runnable example:
[`examples/python/02-policies/time_critical.py`](../examples/python/02-policies/time_critical.py).

## What the host owns

The host keeps the user relationship and the world around the decision:

- memory, history and apps;
- connectors and event streams;
- proactivity and interruption policy;
- permissions and approvals;
- missions, dispatch and execution;
- the user interface.

LAIX keeps the decision and its record.

## Read next

- [Architecture](architecture.md) — the full picture.
- [Host integration](host-integration.md) — the six things a host team checks first.
- [The Decision response](core/01-decision-contract.md) — every field in plain language.
