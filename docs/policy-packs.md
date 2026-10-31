# Policy packs

LAIX ships eight reference policies for decision classes beyond attention and action. With those two
common policies, the layer covers ten decision classes. Each pack is a small, deterministic seed: a
clear contract and a defensible default, not a finished research algorithm. An app can use a pack
directly, wrap it, or replace it with a learned policy behind the same plugin interface.

All packs are exported from the one public API:

```python
from laix import Layer, ReplanningPolicy

decision = Layer(policy=ReplanningPolicy()).decide(request)[0]
```

Inputs are read from `DecisionRequest.attributes`. None of the packs names an app, domain or vendor.

## Active perception

`ActivePerceptionPolicy` chooses whether to look before deciding.

| Input | Meaning |
|---|---|
| `uncertainty` | how unsure the layer is, `0..1` |
| `observations` | candidates with `id`, `information_gain`, `cost` |
| `min_information_gain` | gain below which looking is not worth it |
| `budget` | maximum cost of one observation |

- Low uncertainty returns `wait` with `uncertainty_low`.
- The best observation by gain per cost returns `observe`.
- No affordable or useful observation returns `wait`.

## Safety-constrained action

`SafetyConstrainedPolicy` acts only inside a hard risk limit.

| Input | Meaning |
|---|---|
| `options` | candidates with `id`, `benefit`, `risk`, `cost`, `destructive` |
| `risk_limit` | maximum acceptable risk |
| `safety_blocked` | a hard external block |

- A block returns `wait` with `safety_blocked`.
- No option under the limit returns `wait` with `no_safe_option`.
- The best safe option returns `act`, or `guide` when the benefit is small.
- A destructive or approval-marked option sets `requires_approval`.

## Replanning

`ReplanningPolicy` chooses a replacement plan after the old one breaks.

| Input | Meaning |
|---|---|
| `plans` | candidates with `id`, `success_probability`, `cost`, `deadline_risk` |
| `min_success` | lowest acceptable success probability |
| `max_cost` | highest acceptable cost |
| `risk_weight` | weight on cost against success |

- No feasible plan returns `ask` for a changed constraint.
- Otherwise the best feasible plan returns `act` with an `adopt_plan` intent.

## Allocation

`AllocationPolicy` chooses a portfolio under a budget.

| Input | Meaning |
|---|---|
| `requests` | candidates with `id`, `value`, `cost`, `risk` |
| `budget` | total spend |
| `max_risk` | per-request risk limit |

- Requests are ranked by value per cost.
- The policy funds in order while the budget allows.
- Nothing affordable returns `wait`.
- Otherwise it returns `act` with an `allocate` intent listing the chosen ids.

## Negotiation

`NegotiationPolicy` answers one offer at a time.

| Input | Meaning |
|---|---|
| `offer` | the current offer |
| `reservation` | the worst acceptable value |
| `target` | the preferred value |
| `round`, `max_rounds` | negotiation progress |

- An offer at or above the reservation returns `act` with an `accept_offer` intent.
- The round limit without an acceptable offer returns `escalate`.
- Otherwise it returns `act` with a `counter_offer` between offer and target.

## Preference elicitation

`PreferenceElicitationPolicy` asks the question that best reduces uncertainty.

| Input | Meaning |
|---|---|
| `uncertainty` | preference uncertainty, `0..1` |
| `questions` | candidates with `id`, `information_gain`, `cost` |
| `uncertainty_threshold` | level below which no question is needed |

- Low uncertainty returns `act` with `preference_known`.
- No question available returns `wait`.
- Otherwise the best question by gain per cost returns `ask` with an `ask_question` intent.

## Verification

`VerificationPolicy` confirms that an action did what it claimed.

| Input | Meaning |
|---|---|
| `verified` | the outcome is already confirmed |
| `confidence`, `required_confidence` | current and required confidence |
| `verification_due` | whether a check is still required |
| `checks` | candidates with `id`, `confidence_gain`, `cost` |
| `budget` | maximum cost of one check |
| `escalation_target` | who confirms when no check exists |

- An already confirmed outcome returns `wait` with `already_verified`.
- No check and enough confidence returns `wait` with `verification_not_needed`.
- No affordable or useful check returns `escalate` with a target.
- Otherwise the best check by gain per cost returns `verify` with a `verify` intent.

## Escalation

`EscalationPolicy` decides when a situation must leave the current owner.

| Input | Meaning |
|---|---|
| `resolved` | the situation is already handled |
| `severity`, `severity_threshold` | current severity and the trigger |
| `attempts`, `max_attempts` | repeated attempts and the limit |
| `confidence`, `min_confidence` | confidence and its floor |
| `sla_breached` | a service level is missed |
| `target` | who takes over |

- A resolved situation returns `wait` with `resolved`.
- Conditions inside their limits return `wait` with `within_limits`.
- A trigger without a target returns `ask` with `target_required`.
- Otherwise it returns `escalate` with an `escalation` target and reason.

## Using a pack with the layer

```python
from laix import DecisionRequest, Layer, AllocationPolicy

layer = Layer(policy=AllocationPolicy())
decisions = layer.decide(
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
)
```

Register several packs and select one at runtime:

```python
layer.register_policy("safety", SafetyConstrainedPolicy())
layer.register_policy("replan", ReplanningPolicy())
layer.use_policy("replan")
```

## What these packs are not

- They are not tuned on real data.
- They do not learn or negotiate strategically.
- They do not replace the app's domain rules.

They exist so the decision class has a contract, a default and tests before an app needs it. A real
implementation replaces the policy, not the interface.
