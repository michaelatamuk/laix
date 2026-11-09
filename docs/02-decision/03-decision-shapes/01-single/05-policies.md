# Policies

A policy is a rule set with a name and a `decide(request)` method. It returns one or more
`Decision` objects. A **decision class** is the kind of question a policy answers.

```python
from laix import DecisionRequest, ReplanningPolicy, decide

decision = decide(
    DecisionRequest(subject="pick a plan", at="2026-11-01T10:00:00+00:00"),
    policy=ReplanningPolicy(),
)[0]
```

Most policies read their inputs from `DecisionRequest.attributes`. `PlanningPolicy` takes a
`CommitmentLedger` in its constructor; the wrappers read the request's target and recipients.

## The policy contract

```python
class DecisionPolicy(Protocol):
    name: str

    def decide(self, request) -> list[Decision]: ...
```

`name` is used as the default `policy_version`. A policy may return several decisions. The decision layer
normalizes each one, adds ids and carries the request's confidence provenance. See
[Dispatch](../../01-contract/04-dispatch.md).

`DecisionPolicyRegistry` is a name-to-policy map:

```python
registry = DecisionPolicyRegistry()
registry.register("safety", SafetyConstrainedPolicy())
registry.register("replan", ReplanningPolicy())

decision = decide(request, policy=registry.get("replan"))[0]
```

`register` validates the registered name and the `decide` method, and replaces an existing name.
`get` raises `DecisionPolicyError` for an unknown name. `names()` returns the registered names in sorted
order.

## Built-in action policy

The default action path uses `ActionPolicy`. It reads a `Situation`, the options and merged request
attributes. It chooses by verb band rather than by one utility score.

`dispatch` calls `ActionPolicy` directly and wraps its single `Decision` in a list. `ActionPolicy`
is not a `DecisionPolicy` plugin: it has no `name` and its `decide` returns one `Decision`, while the generic
policy contract returns a list.

`decide_action(request, config=None, **kwargs)` is the functional shortcut when the host does not
need a policy object.

### Admission

Before choosing a verb, `ActionPolicy` removes options that break a hard `Situation` constraint:

| Constraint kind | Compared with |
|---|---|
| `latency` | `ActionOption.latency_ms` |
| `cost` | `ActionOption.cost` |
| `budget` | `ActionOption.cost` |
| `risk` | `ActionOption.risk` |
| `interruption` | `ActionOption.interrupt_cost` |

A hard `safety` constraint with a truthy value blocks every action. Blocked options are reported in
`Decision.alternatives` with the reason that removed them. The blocked reasons are also collected
in `Decision.constraints_applied`.

### Verb order

The policy checks the bands in this order and stops at the first match:

| Order | Condition | Verb |
|---:|---|---|
| 1 | A hard safety constraint blocks action | `wait` |
| 2 | A deadline or safety boundary is breached and an `escalate` option exists | `escalate` |
| 3 | More information is needed or uncertainty is high, and an `observe` option exists | `observe` |
| 4 | Uncertainty is high or confidence is below the floor, and an `ask` option exists | `ask` |
| 5 | Verification is due and a `verify` option exists | `verify` |
| 6 | Urgency and confidence both clear the act thresholds, and an `act` option exists | `act` |
| 7 | Urgency clears the guide threshold, and a `guide` option exists | `guide` |
| 8 | A `wait` option exists | `wait` |
| 9 | Any admissible option remains | its verb |
| 10 | Nothing is admissible | `wait` |

Every decision carries `reason_code="policy_rule"`. The rationale names the threshold that fired.
`policy_version` is `ACTION_POLICY_VERSION` (`0.8.0`), `situation_id` is the situation id, `score` is
the chosen option's `utility` (or `0.0`), and `attributes` records the urgency, uncertainty and flags
the policy used.

`confidence` comes from `Situation.confidence()` unless the merged attributes carry `confidence`.
`uncertainty` defaults to `1 - confidence`; `urgency` defaults to `0.5`; the boolean flags default to
`False`.

### Thresholds

`ActionPolicyConfig` is explicit and tunable:

| Field | Default | Meaning |
|---|---:|---|
| `min_confidence` | 0.55 | Below this, the policy considers asking. |
| `act_confidence` | 0.80 | Minimum confidence for `act`. |
| `ask_uncertainty` | 0.45 | At or above this, the policy considers observing or asking. |
| `act_urgency` | 0.75 | Minimum urgency for `act`. |
| `guide_urgency` | 0.45 | Minimum urgency for `guide`. |
| `max_alternatives` | 6 | Maximum alternative rows. |

The request attributes that drive the bands are `confidence`, `uncertainty`, `urgency`,
`deadline_breached`, `safety_breached`, `verification_due` and `needs_more_info`.

`ActionPolicyConfig` also declares `max_risk`, `max_interrupt` and `approval_kinds`. The current
action policy uses the six thresholds above; hard limits come from `Situation.constraints`, and
approval comes from the chosen option or an approval constraint.

When the chosen verb is `act` and the option needs approval, the decision sets
`requires_approval=True` and adds `approval:human-required` to `constraints_applied`.

### Option ordering

Within one verb band, the policy chooses the option with the highest `ActionOption.utility`:

```text
utility = expected_benefit - 0.25 × risk - 0.15 × interrupt_cost
```

Ties break by `id`. `ActionOption.destructive=True` implies `requires_approval=True`.

## The eight packaged policies

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

### Active perception

Inputs: `uncertainty`, `observations` (`id`, `information_gain`, `cost`), `min_information_gain`,
`budget`.

- `wait` with `uncertainty_low` when uncertainty is below the minimum.
- `wait` with `no_observation` when no observation is available.
- `wait` with `observation_not_worth_it` when the best gain is below the minimum or the cost exceeds
  the budget.
- `observe` with `observe_for_information` when a useful observation exists. The chosen observation
  maximises `information_gain × uncertainty / cost`.

### Safety-constrained action

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

### Replanning

Inputs: `plans` (`id`, `success_probability`, `cost`, `deadline_risk`, `requires_approval`),
`min_success`, `max_cost`, `risk_weight`.

- `ask` with `no_feasible_plan` when no plan meets the success and cost limits.
- `act` with `replan` on the best feasible plan. The option score is
  `success_probability - risk_weight × cost - deadline_risk`.

### Allocation

Inputs: `requests` (`id`, `value`, `cost`, `risk`), `budget`, `max_risk`,
`requires_approval`.

- `wait` with `nothing_affordable` when no request fits the budget and risk limit.
- `act` with `allocate` for a portfolio chosen by value per cost, without exceeding the budget.

The decision's `intent` is `Intent("allocate", {"ids": [...]})`.

### Negotiation

Inputs: `offer`, `reservation`, `target`, `round`, `max_rounds`.

- `act` with `accept_offer` when the offer meets the reservation.
- `escalate` with `round_limit` when the round limit is reached.
- `act` with `counter_offer` otherwise. The counter is
  `max(reservation, (offer + target) / 2)`.

### Preference elicitation

Inputs: `uncertainty`, `questions` (`id`, `information_gain`, `cost`),
`uncertainty_threshold`.

- `act` with `preference_known` when uncertainty is at or below the threshold.
- `wait` with `no_question` when no question is available.
- `ask` with `ask_preference` for the question with the best gain per cost.

### Verification

Inputs: `verified`, `confidence`, `required_confidence`, `verification_due`,
`checks` (`id`, `confidence_gain` or `information_gain`, `cost`), `budget`,
`escalation_target`.

- `wait` with `already_verified` when the outcome is confirmed.
- `wait` with `verification_not_needed` when no check is due and confidence meets the requirement.
- `escalate` with `no_verification_path` when no check can confirm the outcome.
- `escalate` with `no_verification_budget` when every check exceeds the budget.
- `verify` with `verify_outcome` for the check with the best gain per cost.

### Escalation

Inputs: `resolved`, `severity`, `severity_threshold`, `attempts`, `max_attempts`, `confidence`,
`min_confidence`, `sla_breached`, `target`.

- `wait` with `resolved` when the situation is resolved.
- `wait` with `within_limits` when no escalation trigger fires.
- `ask` with `target_required` when a trigger fires but no target is known.
- `escalate` with `escalate_to_target` when a trigger fires and a target is known.

The triggers are severity at or above the threshold, attempts at or above the maximum, confidence
below the minimum, or a breached service level.

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

## The planner bridge

`PlannerPolicy` adapts a `Planner` to the policy interface. The
[planner contract](../../01-contract/02-planner-contract.md) defines the adapter, `PlannerInput` and
`PlannerResult`.

## Replace a policy

Keep the `name`, return `Decision` objects and add bench cases before changing behaviour. A custom
policy can replace any packaged policy without changing the request or the response handling.

## Where the code lives

| Path | Contents |
|---|---|
| `decision/policies/decision_policy.py` | the `DecisionPolicy` protocol |
| `decision/policies/decision_policy_registry.py` | `DecisionPolicyRegistry` |
| `decision/policies/implementations/action.py` | the built-in `ActionPolicy` |
| `decision/policies/implementations/` | the eight decision-class policies, `RulePolicy`, `PlanningPolicy`, the wrappers and `BanditPolicy` |
| `decision/policies/simulation.py` | `ShadowPolicy` and `simulate` |
| `decision/contract/planner_policy.py` | `PlannerPolicy` |

## Examples

- Python: `examples/python/decision/decision/single/policies/`
- TypeScript: `examples/typescript/decision/decision/single/policies/`

## Related

- [Dispatch](../../01-contract/04-dispatch.md)
- [Commitments](../../02-domain/02-commitments.md)
- [Planner contract](../../01-contract/02-planner-contract.md)
- [Outcomes](../../02-domain/03-outcomes.md)
- [Evaluation](../../06-evaluation/01-cases.md)
