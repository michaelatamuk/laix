# Packaged policies

A policy is a rule set with a name and a `decide(request)` method. A **decision class** is the kind
of question a policy answers. LAIX ships eight packaged policies that you pass to `decide` explicitly.

```python
from laix import ReplanningPolicy, decide

decision = decide(request, policy=ReplanningPolicy())[0]
```

The policy reads its inputs from `DecisionRequest.attributes`.

## The eight policies

| Decision class | Policy class | Question | Result |
|---|---|---|---|
| Active perception | `ActivePerceptionPolicy` | Should we look first? | `observe` / `wait` |
| Safety-constrained action | `SafetyConstrainedPolicy` | Is the option safe? | `act` / `guide` / `wait` |
| Replanning | `ReplanningPolicy` | Which plan fits? | `act` / `ask` |
| Allocation | `AllocationPolicy` | What fits the budget? | `act` / `wait` |
| Negotiation | `NegotiationPolicy` | Accept, counter or escalate? | `act` / `escalate` |
| Preference elicitation | `PreferenceElicitationPolicy` | Which question should we ask? | `ask` / `act` / `wait` |
| Verification | `VerificationPolicy` | Did the option work? | `verify` / `wait` / `escalate` |
| Escalation | `EscalationPolicy` | Should we hand over? | `escalate` / `ask` / `wait` |

TypeScript exports the same classes.

Attention and action decisions are built in: `decide` selects them from the request shape. The eight
policies above are selected explicitly. They are deterministic defaults; replace one when your
domain has better rules.

## Use a policy

Pass the policy directly:

```python
from laix import AllocationPolicy, DecisionRequest, decide

decision = decide(
    DecisionRequest(
        subject="weekly work",
        at="2026-11-01T10:00:00+00:00",
        attributes={
            "budget": 10,
            "requests": [
                {"id": "a", "value": 6, "cost": 4},
                {"id": "b", "value": 5, "cost": 6},
            ],
        },
    ),
    policy=AllocationPolicy(),
)[0]
```

Or keep a registry and choose one by name:

```python
from laix import PolicyRegistry, ReplanningPolicy, SafetyConstrainedPolicy, decide

registry = PolicyRegistry()
registry.register("safety", SafetyConstrainedPolicy())
registry.register("replan", ReplanningPolicy())

decision = decide(request, policy=registry.get("replan"))[0]
```

`register` stores a policy. `get` returns it.

## Active perception

- **Inputs:** `uncertainty`, `observations` (`id`, `information_gain`, `cost`),
  `min_information_gain`, `budget`.
- **Result:** `observe` the best gain per cost. `wait` when uncertainty is low or the look costs
  more than it resolves.

## Safety-constrained action

- **Inputs:** `options` (`id`, `benefit`, `risk`, `cost`, `destructive`), `risk_limit`,
  `safety_blocked`.
- **Result:** `act` on the best option inside the risk limit, or `guide` when the benefit is small.
  `wait` when no safe option exists.

## Replanning

- **Inputs:** `plans` (`id`, `success_probability`, `cost`, `deadline_risk`), `min_success`,
  `max_cost`, `risk_weight`.
- **Result:** `act` on the best feasible plan. `ask` when no plan fits.

## Allocation

- **Inputs:** `requests` (`id`, `value`, `cost`, `risk`), `budget`, `max_risk`.
- **Result:** `act` with the chosen ids, ranked by value per cost. `wait` when no request fits.

## Negotiation

- **Inputs:** `offer`, `reservation`, `target`, `round`, `max_rounds`.
- **Result:** `act` to accept or counter. `escalate` at the round limit.

## Preference elicitation

- **Inputs:** `uncertainty`, `questions` (`id`, `information_gain`, `cost`),
  `uncertainty_threshold`.
- **Result:** `ask` the best question. `act` when uncertainty is low. `wait` when there is no question.

## Verification

- **Inputs:** `verified`, `confidence`, `required_confidence`, `verification_due`, `checks` (`id`,
  `confidence_gain`, `cost`), `budget`, `escalation_target`.
- **Result:** `verify` the best check. `wait` when no check is needed. `escalate` when no check
  exists.

## Escalation

- **Inputs:** `resolved`, `severity`, `severity_threshold`, `attempts`, `max_attempts`, `confidence`,
  `min_confidence`, `sla_breached`, `target`.
- **Result:** `escalate` to the target. `ask` when the target is missing. `wait` inside the limits.

## Replace a policy

Keep the policy name, return the same decision shape, and add bench cases before changing behaviour.

The packaged policies are starting points. Your domain policy can replace one without changing the
decision shape.

## Where the rules live

- Action policy: `packages/python/laix/src/laix/core/engines/policies/implementations/action.py`
- Attention policy: `packages/python/laix/src/laix/core/engines/attention/decide.py`
- Packaged policies: `packages/python/laix/src/laix/core/engines/policies/implementations/`
