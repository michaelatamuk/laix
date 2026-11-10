# Packaged policies

Pass a packaged policy explicitly. They are deterministic defaults and read only
`DecisionRequest.attributes`.

Most packaged policies attach an `Intent` for the chosen action, observation, question, check or
handover. The host executes the capability; the policy does not.

| Decision class | DecisionPolicy class | Question | Verbs | Reason codes |
|---|---|---|---|---|
| Active perception | `ActivePerceptionPolicy` | Should we look first? | `observe`, `wait` | `observe_for_information`, `uncertainty_low`, `no_observation`, `observation_not_worth_it` |
| Safety-constrained action | `SafetyConstrainedPolicy` | Is the option safe? | `act`, `guide`, `wait` | `safe_action`, `safe_to_show`, `safety_blocked`, `no_safe_option` |
| Replanning | `ReplanningPolicy` | Which plan fits? | `act`, `ask` | `replan`, `no_feasible_plan` |
| Allocation | `AllocationPolicy` | What fits the budget? | `act`, `wait` | `allocate`, `nothing_affordable` |
| Negotiation | `NegotiationPolicy` | Accept, counter or escalate? | `act`, `escalate` | `accept_offer`, `counter_offer`, `round_limit` |
| Preference elicitation | `PreferenceElicitationPolicy` | Which question should we ask? | `ask`, `act`, `wait` | `ask_preference`, `preference_known`, `no_question` |
| Verification | `VerificationPolicy` | Did the option work? | `verify`, `wait`, `escalate` | `verify_outcome`, `already_verified`, `verification_not_needed`, `no_verification_path`, `no_verification_budget` |
| Escalation | `EscalationPolicy` | Should we hand over? | `escalate`, `ask`, `wait` | `escalate_to_target`, `target_required`, `resolved`, `within_limits` |

## Active perception

Inputs: `uncertainty`, `observations` (`id`, `information_gain`, `cost`), `min_information_gain`,
`budget`.

- `wait` with `uncertainty_low` when uncertainty is below the minimum.
- `wait` with `no_observation` when no observation is available.
- `wait` with `observation_not_worth_it` when the best gain is below the minimum or the cost exceeds
  the budget.
- `observe` with `observe_for_information` when a useful observation exists. The chosen observation
  maximises `information_gain × uncertainty / cost`.

## Safety-constrained action

Inputs: `options` (`id`, `benefit`, `risk`, `cost`, `requires_approval`, `destructive`),
`risk_limit`, `safety_blocked`.

- `wait` with `safety_blocked` when the hard safety flag is set.
- `wait` with `no_safe_option` when every option exceeds `risk_limit`.
- `act` with `safe_action` when the best safe option has benefit at least `0.5`.
- `guide` with `safe_to_show` when the benefit is below `0.5`.

The option score is `benefit - risk - 0.1 × cost`. The decision carries
`Intent("act", {"id": <chosen>})` for the chosen option.

The policy attaches that intent in both the `act` and the `guide` case. A host that shows the option
rather than running it should treat the intent as a proposal, not as a command.

## Replanning

Inputs: `plans` (`id`, `success_probability`, `cost`, `deadline_risk`, `requires_approval`),
`min_success`, `max_cost`, `risk_weight`.

- `ask` with `no_feasible_plan` when no plan meets the success and cost limits.
- `act` with `replan` on the best feasible plan. The option score is
  `success_probability - risk_weight × cost - deadline_risk`.

## Allocation

Inputs: `requests` (`id`, `value`, `cost`, `risk`), `budget`, `max_risk`,
`requires_approval`.

- `wait` with `nothing_affordable` when no request fits the budget and risk limit.
- `act` with `allocate` for a portfolio chosen by value per cost, without exceeding the budget.

The decision's `intent` is `Intent("allocate", {"ids": [...]})`.

## Negotiation

Inputs: `offer`, `reservation`, `target`, `round`, `max_rounds`.

- `act` with `accept_offer` when the offer meets the reservation.
- `escalate` with `round_limit` when the round limit is reached.
- `act` with `counter_offer` otherwise. The counter is
  `max(reservation, (offer + target) / 2)`.

## Preference elicitation

Inputs: `uncertainty`, `questions` (`id`, `information_gain`, `cost`),
`uncertainty_threshold`.

- `act` with `preference_known` when uncertainty is at or below the threshold.
- `wait` with `no_question` when no question is available.
- `ask` with `ask_preference` for the question with the best gain per cost.

## Verification

Inputs: `verified`, `confidence`, `required_confidence`, `verification_due`,
`checks` (`id`, `confidence_gain` or `information_gain`, `cost`), `budget`,
`escalation_target`.

- `wait` with `already_verified` when the outcome is confirmed.
- `wait` with `verification_not_needed` when no check is due and confidence meets the requirement.
- `escalate` with `no_verification_path` when no check can confirm the outcome.
- `escalate` with `no_verification_budget` when every check exceeds the budget.
- `verify` with `verify_outcome` for the check with the best gain per cost.

## Escalation

Inputs: `resolved`, `severity`, `severity_threshold`, `attempts`, `max_attempts`, `confidence`,
`min_confidence`, `sla_breached`, `target`.

- `wait` with `resolved` when the situation is resolved.
- `wait` with `within_limits` when no escalation trigger fires.
- `ask` with `target_required` when a trigger fires but no target is known.
- `escalate` with `escalate_to_target` when a trigger fires and a target is known.

The triggers are severity at or above the threshold, attempts at or above the maximum, confidence
below the minimum, or a breached service level.

## Planning policy

`PlanningPolicy(ledger)` reads the ledger it was constructed with:

- `act` with `due_commitment` when the next actionable commitment is due;
- `wait` with `not_due` when it is not due yet;
- `ask` with `blocked_commitment` when every open commitment is blocked;
- `wait` with `no_commitment` when there is no open commitment.

```python
from laix import DecisionRequest, PlanningPolicy, decide

decision = decide(
    DecisionRequest(subject="next step", at="2026-11-01T10:00:00+00:00"),
    policy=PlanningPolicy(ledger),
)[0]
```

See [Commitments](../../02-domain/02-commitments.md).

## Authoring

`Rule` and `RulePolicy` build a deterministic policy from request attributes.

```python
from laix import DecisionRequest, Rule, RulePolicy

policy = RulePolicy(
    [
        Rule(when={"amount": {"gte": 500}}, verb="ask", reason_code="over_limit"),
        Rule(when={"priority": "high"}, verb="act", reason_code="priority"),
    ]
)
```

Operators inside `when`:

| Operator | Meaning |
|---|---|
| equality | `actual == expected` |
| `gte` | `actual >= value` |
| `lte` | `actual <= value` |
| `in` | `actual in value` |
| `contains` | `value in actual` |

The first matching rule wins. A rule can set `rationale`, `confidence`, `action_id`,
`requires_approval` and `intent`. The default fallback is `wait` with `no_rule`.

## Wrappers

| Wrapper | What it adds |
|---|---|
| `TargetedPolicy` | Sets `target` and `recipients`. `target="request"` takes the mode from the request. |
| `GroupPolicy` | Sets a group target and masks private attributes and evidence. |
| `ShadowPolicy` | Runs a second policy beside the primary and records differences. |
| `simulate` | Runs a policy over recorded requests without side effects. |

### `GroupPolicy`

`GroupPolicy` applies a target and removes private data before sharing:

- `private_attributes` masks matching keys in `attributes`, `intent.args` and alternative payloads;
- `private_evidence` drops evidence whose id, kind or source matches;
- `rationale=` and `undo_hint=` replace those fields;
- `target` defaults to `some`; `recipients` fall back to the request recipients.

Apply it outermost when its target and recipients should win. Its masking applies at any position.

### `ShadowPolicy`

`ShadowPolicy(primary, shadow)` returns the primary decisions and records a `ShadowDifference`
when the `(verb, action_id, reason_code)` signature differs. It does not change the answer.

## Learned policy

`BanditPolicy` puts `UCBBandit` behind the policy interface. It reads arms from
`DecisionRequest.attributes["arms"]` or from the bandit, respects `max_risk`, `budget` and
`exclude`, and returns:

- `wait` with `no_arms` when the learner has no arm;
- `wait` with `no_arm_within_limits` when every arm breaks a limit;
- `act` with `bandit_choice` for the chosen arm.

`record(arm_id, reward)` updates one arm. `learn(outcomes, arm_of)` learns from labelled outcomes.
See [Outcomes](../../02-domain/03-outcomes.md).

## Related

- [Policies overview](README.md)
- [Policy contract](01-policy-contract.md)
- [Commitments](../../02-domain/02-commitments.md)
- [Outcomes](../../02-domain/03-outcomes.md)
