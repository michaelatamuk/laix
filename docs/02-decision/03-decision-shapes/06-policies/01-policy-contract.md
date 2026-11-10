# The policy contract

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

## The planner bridge

`PlannerPolicy` adapts a `Planner` to the policy interface. The
[planner contract](../../01-contract/02-planner-contract.md) defines the adapter, `PlannerInput` and
`PlannerResult`.

## Replace a policy

Keep the `name`, return `Decision` objects and add bench cases before changing behaviour. A custom
policy can replace any packaged policy without changing the request or the response handling.

## Related

- [Policies overview](README.md)
- [Packaged policies](02-packaged-policies.md)
- [Dispatch](../../01-contract/04-dispatch.md)
- [Planner contract](../../01-contract/02-planner-contract.md)
