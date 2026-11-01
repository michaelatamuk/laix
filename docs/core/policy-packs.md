# Policy packs

A **policy** is a rule set that reads a request and returns a decision. A **decision class** is a
kind of question, such as “should we look first?” or “which plan fits?”

Attention and action are built in because `Layer` uses their request shapes to choose a policy. The
other eight are ordinary policy objects selected explicitly. LAIX ships them as packaged policies:

```python
from laix import Layer, ReplanningPolicy

decision = Layer(policy=ReplanningPolicy()).decide(request)[0]
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

TypeScript exports the same classes. Verb meanings are in
[reading a decision](decisions.md).

## Packaged, not examples

These classes are part of the `laix` package. They run when you select them and are covered by tests.
They are not example scripts.

`examples/python/policies/safety.py` is an example that calls `SafetyConstrainedPolicy`. The policy
itself lives in `packages/python/laix/src/laix/policies/safety.py`.

The packaged policies are simple deterministic defaults. Replace one when your domain has better
rules.

## Active perception

- **Inputs:** `uncertainty`, `observations` (`id`, `information_gain`, `cost`),
  `min_information_gain`, `budget`.
- **Result:** `observe` the best gain per cost. `wait` when uncertainty is low or the look is not
  worth it.

## Safety-constrained action

- **Inputs:** `options` (`id`, `benefit`, `risk`, `cost`, `destructive`), `risk_limit`,
  `safety_blocked`.
- **Result:** `act` on the best option inside the risk limit, or `guide` when the benefit is small.
  `wait` when nothing is safe.

## Replanning

- **Inputs:** `plans` (`id`, `success_probability`, `cost`, `deadline_risk`), `min_success`,
  `max_cost`, `risk_weight`.
- **Result:** `act` on the best feasible plan. `ask` when no plan fits.

## Allocation

- **Inputs:** `requests` (`id`, `value`, `cost`, `risk`), `budget`, `max_risk`.
- **Result:** `act` with the chosen ids, ranked by value per cost. `wait` when nothing fits.

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
from laix import AllocationPolicy, DecisionRequest, Layer

layer = Layer(policy=AllocationPolicy())
decision = layer.decide(
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
    )
)[0]
```

Register several and choose one:

```python
layer.register_policy("safety", SafetyConstrainedPolicy())  # store
layer.register_policy("replan", ReplanningPolicy())         # store
layer.use_policy("replan")                                  # activate
```

`register_policy` stores a policy. `use_policy` makes it active.

## Replace a pack

Keep the policy name, return the same decision shape, and add bench cases before changing behaviour.

The packs are starting points. Your domain policy can replace one without changing the layer.
