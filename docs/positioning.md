# LAIX and decision models

People sometimes compare LAIX with a decision model such as JEV. They are different kinds of thing,
and they often work together.

## Two kinds of thing

| Kind | Question it answers | Examples |
|---|---|---|
| **Decision model** | What is the answer to this question? | JEV, a classifier, an LLM judge, an expected-utility model |
| **Decision layer** | What should the app do next, and what happened? | LAIX |

A decision model produces a judgment. A decision layer turns a judgment into an action with approval,
execution, verification and records.

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
one verb + reason + approval + action details
              ↓
execute -> receipt -> outcome
```

LAIX works with any model. Its built-in policies are deterministic rules. Its bandit policy is a
small learner. A JEV call can sit behind a LAIX policy.

## Side by side

| | JEV | LAIX |
|---|---|---|
| Kind | Decision model | Decision layer |
| Input | State + typed question | Request + options + limits |
| Output | Typed answer + probabilities | Verb + reason + action and approval |
| Main value | calibrated judgment | decision semantics and lifecycle |
| Execution | host | host |
| Approval, undo, receipts | host policy | LAIX app kit |
| Records outcomes | host | LAIX ledger |
| Learns | The model is fixed or calibrated | Optional bandit policy |
| Vendor | A specific model | Model-agnostic |

## Where they overlap

Both can choose among a fixed set of options. In the leak example:

- the state is “water is coming under the door, urgency is high”;
- the options are “wait, look closer, ask the owner, turn off the valve, call the manager”;
- both LAIX and JEV can return “turn off the valve”.

So the action choice itself is the same kind of problem.

The difference is how the choice is made and what happens around it.

| Step | LAIX action policy | JEV |
|---|---|---|
| Read the situation | beliefs, constraints, urgency | state text or context |
| Read the options | `Action` objects | allowed answers |
| Remove unsafe options | filters hard constraints first | states them in the question |
| Choose | threshold rules plus utility | model probabilities |
| Confidence | belief or attribute | calibrated confidence |
| Output | full `Decision` | choice plus probabilities |
| Lifecycle | approval, execution, verify | judgment only |

LAIX’s built-in action policy is itself a small decision model: a rule-based one. JEV is a different
kind of decision model: a calibrated classifier over typed answers.

The useful distinction:

- **JEV can be the chooser** inside a policy.
- **LAIX is the layer** that filters unsafe options, applies approval, executes, verifies and records.

If JEV replaces the LAIX action policy, LAIX still adds the lifecycle around the choice.

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
| Action names | `pay_invoice` |
| Verification | `bank_status` |
| Escalation target | `owner` |
| Outcome metric | payment cleared or failed |

LAIX supplies the generic layer:

- one decision shape;
- hard-constraint filtering;
- the `requires_approval` flag;
- policy selection;
- execution receipts;
- `verify` and `escalate` verbs;
- records and bench.

Could the app do all of this without LAIX? **Yes.** For one payment flow, direct app code is simpler.
LAIX pays off when several flows or apps need the same decision contract, approval rules, execution
receipts and outcome records.

JEV and LAIX both depend on the app for domain meaning:

- JEV turns state into a judgment;
- LAIX turns a request into a decision and a lifecycle;
- the app knows what “pay the invoice” means.

## When LAIX is actually needed

For **one app with one decision**, app code with JEV is a good fit.

JEV plus app code can implement every functional step. LAIX is a prebuilt **shared decision layer**.
It matters when that layer would otherwise be written again in several apps:

- several apps or agents;
- several decision classes per app;
- shared approval and audit rules;
- policies that must be compared or swapped;
- one place to record outcomes and run a bench.

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

With LAIX, the app still keeps the jobs, technicians, photos and payments. LAIX supplies one layer
for all eight decision classes. One approval rule, one execution receipt, one audit shape, one bench.

At this point the team would otherwise be building a decision layer themselves. LAIX is that layer,
already built.

### The simple test

| Situation | Use |
|---|---|
| One app, one decision | App code, possibly with JEV |
| Many apps or many decision classes | LAIX |
| Shared approval, audit, verification and bench | LAIX |
| Policy experiments or shadow comparisons | LAIX |

LAIX replaces the bespoke decision layer an app would otherwise write. JEV and the app’s domain
logic stay in place.

The plan for adding a real engine core is in [the engine roadmap](core/engine-roadmap.md).

## Using them together

A JEV-style model can be an app-side policy:

```python
from laix import LayerDecision

class JevPolicy:
    name = "jev.v1"

    def __init__(self, client):
        self.client = client

    def decide(self, request):
        result = self.client.decide(
            state=request.subject,
            question="Which action fits?",
            options=["wait", "observe", "act", "ask"],
        )
        if result.confidence < 0.6:
            return [LayerDecision(
                verb="ask",
                confidence=result.confidence,
                reason_code="low_confidence",
                rationale="the model is unsure",
            )]
        return [LayerDecision(
            verb=result.choice,
            confidence=result.confidence,
            reason_code="model_choice",
            rationale="the model selected this option",
        )]
```

LAIX still applies the rest:

- approval when `requires_approval` is set;
- execution through the app or platform;
- verification when the outcome matters;
- outcome recording and learning.

The adapter stays in the app. LAIX core stays model-neutral.

## Which one to choose

| Need | Use |
|---|---|
| Classify text into one of a fixed set of labels | JEV or another classifier |
| Score an item on a rubric | JEV or another scorer |
| Decide whether to act, ask, wait or escalate, with approval and records | LAIX |
| Both judgment and decision lifecycle | JEV inside a LAIX policy |

## Why pair them

A model can be confident and wrong. LAIX adds the parts around a judgment:

- risk limits and approval;
- action choice among the options the app can afford;
- verification of the outcome;
- a record of what was decided and what happened.

The useful comparison is:

```text
JEV / classifier / LLM  -> judgment
LAIX                    -> decision, approval, execution, outcome
```

LAIX is the layer that can use a decision model. It works alongside JEV and other models.
