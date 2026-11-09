# What is LAIX?

**LAIX — Live AI Experience — is the live decision layer for AI agents that act in the real world.**

An agent or automation that acts in the real world is always in the loop: it notices what is
changing, decides what matters and acts before the moment passes. LAIX gives that loop a single
decision contract. The host builds the experience; LAIX owns the decision.

> **What matters now, and what should the experience do about it?**

LAIX turns the situation, the options the host can offer and the limits the host sets into one
decision:

```text
wait    observe    guide    ask    act    verify    escalate
```

Then the product does the work.

LAIX provides one decision shape, explicit reasons, confidence, approval and a trail. The host
provides the experience, data, UI, execution and delivery.

## Why a live experience needs a decision layer

A live experience needs timing, restraint, safety, coherence and a record:

- **timely** — act inside the window;
- **restrained** — stay silent when the moment is wrong;
- **safe** — respect hard risk and approval limits;
- **coherent** — one decision shape across attention, action and follow-up;
- **auditable** — record why it intervened and what happened.

LAIX supplies that layer. The host keeps the experience, memory, UI, execution and delivery.

## What LAIX adds

LAIX turns those properties into one decision layer:

- **One contract** — attention, action, follow-up, execution and outcomes return the same decision
  shape with a reason, confidence and trail.
- **Training-free** — the default path is policy/rules based; planners use a model the host supplies.
- **Live decision** - promises, execution risk and human attention are part of the decision;
  calibration and decision time complete the loop.
- **Host control** — LAIX decides; the host owns data, execution, storage and delivery.
- **Evidence** — conformance vectors, bench, examples and Python/TypeScript parity.

The contribution is the combination: a coherent decision layer for live experiences.
`LiveCompositePlanner` makes that concrete: one planner result can keep a promise, avoid an irreversible action
and respect an attention budget at the same time. Calibration and the decision timeline complete the
loop around that planner result.

## Model-optional

Training-free means LAIX does not train or fine-tune a model. The default path is policies and
rules. A planner can use a world model the host supplies: states, transitions and rewards. A
pretrained model can sit behind `PlannerPolicy`, and the decision contract stays the same.

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

LAIX works inside one task. The product keeps its own orchestration.

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

When the task has promises, execution risk or a limited human-attention budget, those are part of
the decision too: what it promises, what could go wrong after the button is pressed, and how much
attention it spends. Later outcomes can calibrate the next decision.

LAIX is training-free: the default path is policy/rules based, and planners use a model the host
supplies.

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
2. **Delay above 6 minutes** leaves the set. A safe option that arrives too late becomes a
   follow-up.

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

- **confidence × benefit** — benefit weighted by the chance the socket is live;
- **risk** — personal injury risk;
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
cheap in risk, but 15 minutes is outside the window, so it becomes a follow-up. Evacuation is fast
and safe, but it leaves the water running and it disrupts the building. Looking is cheap, but at
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

A 2-minute look is cheaper than a 4-minute trip to cut power for a socket whose state is uncertain.
That is the point of the information term: when confidence is low, buying information can beat
acting.

If the dry corridor is blocked, evacuation wins with **0.3475**. The electrician stays the follow-up
in every branch.

This example uses a small policy plugin. The built-in action policy ranks benefit, risk and
interruption cost. An app that needs money, delay, disruption and information value adds those
terms in its own policy.

Runnable example:
[`examples/python/decision/decision/single/policies/time_critical.py`](../../../examples/python/decision/decision/single/policies/time_critical.py).

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

- [Decision lifecycle](02-decision-lifecycle.md) - one loop from moment to outcome.
- [Architecture](../../04-concepts/01-architecture/01-system-architecture.md) — the full picture.
- [Host integration](../02-first-steps/02-host-integration.md) — the six things a host team checks first.
- [The Decision response](../../02-decision/01-contract/01-decision-contract.md) — every field in plain language.
- [FAQ](../../04-concepts/04-reference/02-faq.md) — models, execution and novelty.
