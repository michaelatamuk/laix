# LAIX and decision models

People sometimes compare LAIX with a decision model such as JEV. They are different kinds of thing,
and they often work together.

## Two kinds of thing

| Kind | Question it answers | Examples |
|---|---|---|
| **Decision model** | What is the answer to this question? | JEV, a classifier, an LLM judge, an expected-utility model |
| **Decision layer** | What should this task do next? | LAIX |

A decision model produces a judgment. A decision layer produces a task decision: what the task should do next, with a reason and evidence. The host owns execution, approval and records; the LAIX app kit supplies those surfaces when the host wants them.

## JEV

JEV is a typed decision model from TypeSafe. It takes a state and a question and returns a closed
answer:

```text
state + question + allowed answers
              ↓
choice / score / yes-no
+ probabilities
+ confidence
```

It classifies, scores or judges. The host executes, approves and records.

## LAIX

LAIX takes a request and returns one decision:

```text
situation + options + limits
              ↓
one verb + reason + approval + execution details
              ↓
the host executes, approves and records
```

LAIX works with any model. Its built-in policies are deterministic rules. Its bandit policy is a
small learner. A JEV call can sit behind a LAIX policy.

The decision is the core product. Execution, approval, receipts and records belong to the host, or
to the optional app kit when the host chooses it.

## Side by side

| | JEV | LAIX |
|---|---|---|
| Kind | Decision model | Decision layer |
| Input | State + typed question | Request + options + limits |
| Output | Typed answer + probabilities | Verb + reason + chosen option and approval |
| Main value | calibrated judgment | decision semantics; optional lifecycle with the app kit |
| Execution | host | host |
| Approval, undo, receipts | host policy | LAIX app kit (optional) |
| Records outcomes | host | host, or LAIX app kit |
| Learns | The model is fixed or calibrated | Optional bandit policy |
| Vendor | A specific model | Model-agnostic |

## Where they overlap

Both can choose among a fixed set of options. In the leak example:

- the state is “water is coming under the door, urgency is high”;
- the options are “wait, look closer, ask the owner, turn off the valve, call the manager”;
- both LAIX and JEV can return “turn off the valve”.

So the choice among options is the same kind of problem.

The difference is how the choice is made and what happens around it.

| Step | LAIX action policy | JEV |
|---|---|---|
| Read the situation | beliefs, constraints, urgency | state text or context |
| Read the options | `ActionOption` objects | allowed answers |
| Remove unsafe options | filters hard constraints first | states them in the question |
| Choose | threshold rules plus utility | model probabilities |
| Confidence | belief or attribute | calibrated confidence |
| Output | full `Decision` | choice plus probabilities |
| Around the choice | the host, or app kit, adds approval, execution and verification | judgment only |

LAIX’s built-in action policy is itself a small decision model: a rule-based one. JEV is a different
kind of decision model: a calibrated classifier over typed answers.

The useful distinction:

- **JEV can be the chooser** inside a policy.
- **LAIX is the layer** that filters unsafe options and returns the task decision. The host, or the
  optional app kit, handles approval, execution, verification and records.

If JEV replaces the LAIX action policy, LAIX still supplies the decision contract; the host or app
kit supplies the lifecycle around the choice.

## A decision that needs a host layer

A plumber sends a £480 invoice. The house rule says:

- invoices under £500 may be paid automatically if they match the work order;
- invoices at or above £500 need the owner’s approval;
- after payment, check that the bank confirms it;
- if payment fails, call the owner.

JEV can answer a judgment question:

```text
Does this invoice match the work order?
-> yes, 0.93 confidence
```

That is useful, but it is only one input.

The app defines the invoice, the plumber, the bank and the £500 rule. LAIX sees generic pieces.
The app maps the domain into those pieces:

| App supplies | Example |
|---|---|
| Options | `pay`, `ask`, `verify`, `escalate` |
| Constraints | amount ≥ £500 needs approval |
| Option names | `pay_invoice` |
| Verification | `bank_status` |
| Escalation target | `owner` |
| Outcome metric | payment cleared or failed |

LAIX supplies the generic decision:

- one decision shape;
- hard-constraint filtering;
- the `requires_approval` flag;
- policy selection;
- `verify` and `escalate` verbs.

The optional app kit adds execution receipts, records and the bench. The host runs the chosen option.

Could the app do all of this without LAIX? **Yes.** For one payment flow, direct app code is simpler.
LAIX pays off when several flows or apps need the same decision contract, with the optional app kit
supplying shared approval rules, execution receipts and outcome records.

JEV and LAIX both depend on the app for domain meaning:

- JEV turns state into a judgment;
- LAIX turns a request into a decision; the host or app kit adds the lifecycle;
- the app knows what “pay the invoice” means.

## When LAIX is actually needed

For **one app with one decision**, app code with JEV is a good fit.

JEV plus app code can implement every functional step. LAIX is a prebuilt **shared decision layer**.
It matters when that layer would otherwise be written again in several apps:

- several apps or agents;
- several decision classes per app;
- shared approval and audit rules (the app kit);
- policies that must be compared or swapped;
- one place to record outcomes and run a bench (the app kit).

The question is: do you want every app to build and maintain the same decision layer?

### Example: a home-repair dispatch company

A small company has 10 technicians and 30 jobs a day. Calls, photos and messages arrive all day. The
system must decide:

| Decision | Example |
|---|---|
| Attention | Is this an emergency worth interrupting a technician for? |
| Allocation | Which technician should take the job? |
| Replanning | Should we send a second technician? |
| Safety | Is it safe to enter the building? |
| Negotiation | Should we accept the customer’s price? |
| Ask | Does a €300 extra part need office approval? |
| Verification | Did the technician finish the job? |
| Escalation | Should we call the manager now? |

JEV can judge “is this a gas leak?” or “does this photo show mould?”. The app can dispatch a
technician, charge a card and send a message.

Without a shared layer, the team writes eight separate decision paths, or one ad-hoc engine. Each
path grows its own approval rule, audit format, verification step and tests. They drift apart.

With LAIX, the app still keeps the jobs, technicians, photos and payments. LAIX supplies one
decision contract for all eight decision classes. The optional app kit adds one approval rule, one
execution receipt, one audit shape and one bench.

At this point the team would otherwise be building a decision layer themselves. LAIX is that layer,
already built.

### The simple test

| Situation | Use |
|---|---|
| One app, one decision | App code, possibly with JEV |
| Many apps or many decision classes | LAIX |
| Shared approval, audit, verification and bench | LAIX app kit |
| Policy experiments or shadow comparisons | LAIX |

LAIX replaces the bespoke decision layer an app would otherwise write. JEV and the app’s domain
logic stay in place.

## Using them together

A JEV-style model can be an app-side policy:

```python
from laix import Decision

class JevPolicy:
    name = "jev.v1"

    def __init__(self, client):
        self.client = client

    def decide(self, request):
        result = self.client.decide(
            state=request.subject,
            question="Which option fits?",
            options=["wait", "observe", "act", "ask"],
        )
        if result.confidence < 0.6:
            return [Decision(
                verb="ask",
                confidence=result.confidence,
                reason_code="low_confidence",
                rationale="the model is unsure",
            )]
        return [Decision(
            verb=result.choice,
            confidence=result.confidence,
            reason_code="model_choice",
            rationale="the model selected this option",
        )]
```

The host applies the rest:

- approval when `requires_approval` is set;
- execution through the app or platform;
- verification when the outcome matters.

The optional app kit records the decision, execution and outcome. The adapter stays in the app.
LAIX core stays model-neutral.

## Which one to choose

| Need | Use |
|---|---|
| Classify text into one of a fixed set of labels | JEV or another classifier |
| Score an item on a rubric | JEV or another scorer |
| Decide whether to act, ask, wait or escalate, with approval and records | LAIX core, with the app kit for approval and records |
| Both judgment and decision lifecycle | JEV inside a LAIX policy; app kit for the lifecycle |

## Why pair them

A model can be confident and wrong. LAIX adds the task decision around a judgment:

- risk limits;
- choice among the options the app can afford;
- verification and escalation verbs.

The host, or the optional app kit, adds approval, execution and records.

The useful comparison is:

```text
JEV / classifier / LLM  -> judgment
LAIX core               -> task decision
host / app kit          -> approval, execution, outcome
```

LAIX is the layer that can use a decision model. It works alongside JEV and other models.

## In PPMA, the comparison is different

PPMA's Commander already chooses commands through an LLM ask. There, the relevant comparison is the Commander's LLM ask vs a LAIX policy for one bounded task, not JEV vs LAIX. JEV is a judgment engine that can sit inside either path.

For the PPMA case, see [PPMA + LAIX](ppma-laix.md).
