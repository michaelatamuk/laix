# Policy packs

A **policy** is a rule set that reads a request and returns a decision. A **decision class** is a
kind of question, such as “should we look first?” or “which plan fits?”

Attention and action decisions are built in because `decide` uses their request shapes to choose a policy. The
other eight are ordinary policy objects selected explicitly. LAIX ships them as packaged policies:

```python
from laix import ReplanningPolicy, decide

decision = decide(request, policy=ReplanningPolicy())[0]
```

Inputs come from `DecisionRequest.attributes`. The packs use generic words only.

| Class | Policy | Result |
|---|---|---|
| Active perception | `ActivePerceptionPolicy` | `observe` or `wait` |
| Safety-constrained action | `SafetyConstrainedPolicy` | `act`, `guide` or `wait` |
| Replanning | `ReplanningPolicy` | `act` or `ask` |
| Allocation | `AllocationPolicy` | `act` or `wait` |
| Negotiation | `NegotiationPolicy` | `act` or `escalate` |
| Preference elicitation | `PreferenceElicitationPolicy` | `ask`, `act` or `wait` |
| Verification | `VerificationPolicy` | `verify`, `wait` or `escalate` |
| Escalation | `EscalationPolicy` | `escalate`, `ask` or `wait` |

TypeScript exports the same classes.

## Packaged policies

These classes are part of the `laix` package. They run when you select them and are covered by tests.

`examples/policies/safety.py` is a usage example that calls `SafetyConstrainedPolicy`. The
policy itself lives in `packages/python/laix/src/laix/core/engines/policies/implementations/safety_constrained.py`.

The packaged policies are simple deterministic defaults. Replace one when your domain has better
rules.

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

## Use a pack

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

Register several and choose one:

```python
from laix import PolicyRegistry, ReplanningPolicy, SafetyConstrainedPolicy, decide

registry = PolicyRegistry()
registry.register("safety", SafetyConstrainedPolicy())
registry.register("replan", ReplanningPolicy())

decision = decide(request, policy=registry.get("replan"))[0]
```

`register` stores a policy. `get` returns the active one.

## Replace a pack

Keep the policy name, return the same decision shape, and add bench cases before changing behaviour.

The packs are starting points. Your domain policy can replace one without changing the decision shape.

## Where the rules live

- Action policy: `packages/python/laix/src/laix/core/engines/policies/implementations/action.py`
- Attention policy: `packages/python/laix/src/laix/core/engines/attention/decide.py`
