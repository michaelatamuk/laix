# Single-decision planners

The four live planners each answer the same question: which option is best? They differ in what
they add to the utility score:

| Planner | Adds |
|---|---|
| `UtilityPlanner` | expected utility with hard limits and risk attitude |
| `CommitmentPlanner` | the effect of an option on open promises |
| `ExecutionRiskPlanner` | irreversibility, unknown outcomes, approval and recovery cost |
| `HumanAttentionPlanner` | interruption, approval and escalation cost |

Each is a `Planner`: it implements `solve(problem) -> PlannerResult`. Each is deterministic and
training-free. Each reads its special facts from the option's `params` and from
`PlannerInput.attributes`.

## Shared utility model

The four planners score the ordinary utility with `UtilityModel`:

```python
from laix import UtilityWeights

weights = UtilityWeights(
    benefit=1.0,
    cost=0.25,
    risk=0.25,
    interruption=0.15,
    latency=0.0,
)
```

```text
risk_effective =
    risk                     if risk_attitude == "neutral"
    risk × (1 + risk)        if risk_attitude == "averse"
    risk × (1 - 0.5 × risk)  if risk_attitude == "seeking"

utility = benefit × expected_benefit
        - cost × cost
        - risk × risk_effective
        - interruption × interrupt_cost
        - latency × latency_ms
```

`risk_attitude` is `neutral`, `averse` or `seeking`. `RISK_ATTITUDES` is the tuple of those three
values. The risk attitude changes the risk multiplier in the formula above.

`UtilityModel.feasible(option)` rejects an option when:

- `option.risk > max_risk`;
- `max_cost` is set and `option.cost > max_cost`;
- `max_latency_ms` is set and `option.latency_ms > max_latency_ms`.

The hard `Situation` constraints are enforced separately. A hard constraint for `risk`, `cost`,
`budget`, `latency` or `interruption` blocks the option when its amount exceeds the limit. A hard
`safety` constraint with a truthy value blocks the option. The planner reports the blocked option in
`alternatives` with the blocker in `rejected_because`.

The planner confidence is:

```text
1.0                                      if there is no second option
clamp(0.5 + 0.5 × gap / |best|)          otherwise, gap = max(0, best - second)
```

## Utility planner

`UtilityPlanner` chooses the feasible option with the highest expected utility.

```python
from laix import ActionOption, PlannerInput, UtilityPlanner

plan = UtilityPlanner().solve(
    PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
            ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
        ),
    )
)
print(plan.action_id, plan.reason_code, plan.score)
```

| Item | Value |
|---|---|
| Name | `utility.v1` |
| Success reason | `expected_utility` |
| Empty options | `wait` with `no_options` |
| No feasible option | `wait` with `no_feasible_option` |
| PlannerResult attributes | `utility`, `risk_attitude` |
| Alternatives | `action_id`, `verb`, `name`, `utility`, `rejected_because` |

The planner reads `max_risk`, `max_cost` and `max_latency_ms` from `PlannerInput.attributes`. It
rebuilds the model when at least one limit override is present. To set `risk_attitude`, pass a
`UtilityModel` or include a limit override with the attribute.

`ActionOption.utility` is a separate fixed tie-break value used by the built-in action policy and the
baselines:

```text
expected_benefit - 0.25 × risk - 0.15 × interrupt_cost
```

`UtilityPlanner` uses `UtilityModel.score` instead.

## Commitment planner

`CommitmentPlanner` keeps the utility score and adds the effect of an option on open commitments.

An option declares its effect in `params`. The shape and the accepted aliases are on the
[commitments page](../../02-domain/02-commitments.md#how-commitments-enter-a-decision). `creates` accepts strings
or mappings with an `id`.

| Field | Meaning |
|---|---|
| `fulfills` | Open commitments this option keeps. |
| `violates` | Open commitments this option breaks. |
| `creates` | New commitments this option adds. |
| `hard` | A violation blocks the option instead of only penalising it. |

`CommitmentEffect` carries those four fields. `commitment_effect(option)` reads them from `params`.
`CommitmentScore` carries `utility`, `commitment`, `total`, the fulfilled/violated/created ids, the
due ids and the blocked reason.

The score:

```text
fulfilled          = fulfills ∩ open, not blocked
blocked_fulfilled  = fulfills ∩ open, blocked
violated           = violates ∩ open
created            = creates not already present
due_fulfilled      = fulfilled where the commitment is due
due_violated       = violated where the commitment is due

keep_reward        = Σ keep × (0.5 + priority)      for fulfilled
due_reward         = Σ due × (0.5 + priority)       for due_fulfilled
violation_penalty  = Σ violate × (0.5 + priority)   for violated
due_penalty        = Σ due × (0.5 + priority)       for due_violated
blocked_penalty    = blocked × len(blocked_fulfilled)

commitment = keep_reward + due_reward
             - violation_penalty - due_penalty
             - blocked_penalty
             - create × len(created)

total = utility + commitment
```

Weights:

| Weight | Default |
|---|---:|
| `keep` | 0.35 |
| `violate` | 1.0 |
| `create` | 0.10 |
| `due` | 0.25 |
| `blocked` | 0.50 |

A commitment is blocked when it is missing, any `depends_on` item is missing or not `done`, or any
external dependency has not resolved with enough trust. By default the planner checks the graph with
`require_verified=True`, so a `reported` external commitment does not count as done. Pass
`require_verified=False` to `CommitmentPlanner` when reported dependencies are acceptable, and pass
`max_verification_age` to reject stale `verified` ones. A hard violation sets `blocked` to
`hard commitment: <ids>` and removes the option; fulfilling a hard commitment while it is blocked
sets `blocked hard commitment: <ids>` and removes it too.

Commitments enter the problem through `PlannerInput.attributes["commitments"]` or the alias
`attributes["commitment_ledger"]`. The value may be a `CommitmentLedger`, a mapping with a
`commitments` key, or an iterable of `Commitment` objects or mappings. To include another owner,
pass a `CommitmentGraph` as `attributes["commitment_graph"]`, or pass
`attributes["external_commitments"]` for the planner to build one.

| Item | Value |
|---|---|
| Name | `commitment.v1` |
| Success reason | `commitment_aware` |
| Empty options | `wait` with `no_options` |
| No feasible option | `wait` with `no_feasible_option` |
| Verification | `require_verified=True` by default; optional `max_verification_age` |
| PlannerResult attributes | `utility`, `commitment_score`, `commitments_fulfilled`, `commitments_violated`, `commitments_created`, `commitments_due_fulfilled`, `commitments_blocked_fulfilled`, `commitments_blocked_by` |

`commitments_blocked_by` is a list of owner-qualified blockers:

```text
[{owner, ledger, id, reason}]
```

`reason` is `missing`, `open`, `unverified` or `stale`. Each alternative also carries `blocked_by` with
the same shape and a stable `rejected_reason_code`, so a host can explain a rejected option without
re-running the graph.

See [Commitments](../../02-domain/02-commitments.md) for the ledger and store.

## Execution-risk planner

`ExecutionRiskPlanner` keeps the utility score and adds the cost of acting.

An option declares its facts in `params`:

```python
ActionOption(
    id="archive",
    verb="act",
    name="archive",
    expected_benefit=0.7,
    params={"unknown_risk": 0.2, "recovery_cost": 0.1},
)
```

The facts can also be nested under `params["execution"]`.

```text
irreversible      = not option.reversible
requires_approval = approval or option.requires_approval or option.destructive

execution = -irreversible_weight × (1 if irreversible else 0)
            - unknown_weight × unknown_risk
            - approval_weight × (1 if requires_approval else 0)
            - recovery_weight × recovery_cost

total = utility + execution
```

Weights:

| Weight | Default |
|---|---:|
| `irreversible` | 0.35 |
| `unknown` | 0.5 |
| `approval` | 0.15 |
| `recovery` | 0.25 |

The host can pass execution state in `PlannerInput.attributes`:

```python
attributes={
    "execution_state": {"archive": "unknown"},
    "execution_receipts": receipts,
}
```

| Receipt status | Effect |
|---|---|
| `unknown` | raises `unknown_risk` to at least `1.0` |
| `failed`, `refused`, `cancelled`, `undone` | raises `recovery_cost` to at least `1.0` |
| `pending` | requires approval |
| `approved`, `executed`, `duplicate` | no extra penalty |

`execution_state` is keyed by option id. `execution_receipts` is scanned for a receipt whose
`action_name` matches the option id or name.

`ExecutionEffect` carries `unknown_risk` and `recovery_cost`; `execution_effect(option)` reads them
from `params`. `ExecutionScore` carries `utility`, `execution`, `total`, `irreversible`,
`unknown_risk`, `recovery_cost`, `requires_approval` and `receipt_status`.

| Item | Value |
|---|---|
| Name | `execution.v1` |
| Success reason | `execution_aware` |
| Empty options | `wait` with `no_options` |
| No feasible option | `wait` with `no_feasible_option` |
| PlannerResult attributes | `utility`, `execution_score`, `irreversible`, `unknown_risk`, `recovery_cost`, `requires_approval`, `receipt_status` |

The planner blocks on hard limits and infeasibility. Execution risk is priced rather than blocked.

## Human-attention planner

`HumanAttentionPlanner` treats human attention as a budget. It keeps the utility score and charges
for interruption, approval and escalation.

Signal attention and this planner work at different levels: signal attention ranks the signals the
host sends; this planner prices human involvement when it chooses an action option. See
[Signal attention](../../04-sensing/01-signals.md).

An option can declare its attention facts:

```python
ActionOption(
    id="guide",
    verb="guide",
    name="guide",
    expected_benefit=0.75,
    interrupt_cost=0.8,
    params={"attention": {"requires_approval": False, "escalates": False}},
)
```

The host supplies the budget:

```python
attributes={
    "human_attention_budget": 0.2,
    "human_attention_spent": 0.2,
    "approvals": {"guide": "rejected"},
}
```

`human_attention_budget` may be a number, a mapping with `total` and `spent`, or a `HumanAttentionBudget`.
`human_attention_spent` is subtracted when the budget is a number. `human_attention_remaining` overrides the
computed remainder. A shared `HumanAttentionBudget` can be passed as one object.

The human-attention budget is a planning cost. It is separate from `SignalContext.signal_interruption_budget`, which
caps the number of delivered signal decisions in one attention cycle.

The effect:

```text
cost = interrupt_cost
       + 0.5 if requires_approval
       + 0.5 if escalates
       + 0.5 if interactive
```

`interactive` is true for the `ask` and `guide` verbs. `requires_attention` is true when `cost > 0`
or the option requires approval or escalation.

`HumanAttentionEffect` carries `interrupt_cost`, `requires_approval`, `escalates`, `interactive` and
`approval_state`; `human_attention_effect(option, ...)` reads it from `params`. `HumanAttentionScore` carries
`utility`, `human_attention`, `total`, `effect`, `remaining` and `blocked`.

The score:

```text
attention = -interrupt_weight × interrupt_cost
            - approval_weight × (1 if requires_approval else 0)
            - escalation_weight × (1 if escalates else 0)
            - exhausted_weight × (1 if blocked else 0)

total = utility + human_attention
remaining_after = max(0, remaining - cost)
```

Weights:

| Weight | Default |
|---|---:|
| `interrupt` | 0.4 |
| `approval` | 0.25 |
| `escalation` | 0.3 |
| `exhausted` | 1.0 |

Blocking:

- `approval_state == "rejected"` blocks the option with `approval rejected`;
- an option that requires attention and costs more than the remaining budget blocks with
  `human attention budget exhausted`;
- otherwise the option is admissible.

Approval state comes from `attributes["approvals"]`, keyed by option id or name. The value may be a
boolean, `approved`, `pending` or `rejected`, or a list of records with `action_id`/`action_name`
and `status`. An approved option does not pay the approval cost.

| Item | Value |
|---|---|
| Name | `human-attention.v1` |
| Success reason | `human_attention_aware` |
| Empty options | `wait` with `no_options` |
| No feasible option | `wait` with `approval_rejected` or `human_attention_budget_exhausted` |
| PlannerResult attributes | `utility`, `human_attention_score`, `human_attention_cost`, `human_attention_remaining`, `human_attention_budget_blocked`, `approval_state` |

## Comparison

| Planner | Term | Main inputs | Success reason | Own blocking |
|---|---|---|---|---|
| `UtilityPlanner` | utility | model, option cost/risk/latency, hard constraints | `expected_utility` | infeasible, hard constraint |
| `CommitmentPlanner` | commitment | commitments, option `fulfills`/`violates`/`creates` | `commitment_aware` | hard commitment violation, infeasible |
| `ExecutionRiskPlanner` | execution | reversibility, `unknown_risk`, `recovery_cost`, receipts, approval | `execution_aware` | infeasible, hard constraint |
| `HumanAttentionPlanner` | human attention | `HumanAttentionBudget`, approvals, option attention facts | `human_attention_aware` | approval rejected, budget exhausted, infeasible |

All four share the same `PlannerResult` shape, the same utility model and the same confidence formula. The
[live composite planner](02-composite.md) runs their scoring functions together and returns
one composite plan.

## Examples

- Python: `examples/python/decision/decision/single/planners/utility_planner.py`
- Python: `examples/python/decision/decision/single/planners/commitment_planner.py`
- Python: `examples/python/decision/decision/single/planners/execution_planner.py`
- Python: `examples/python/decision/decision/single/planners/human_attention_planner.py`
- TypeScript: `examples/typescript/decision/decision/single/planners/planners.mts`

## Related

- [Commitments](../../02-domain/02-commitments.md)
- [Planner contract](../../01-contract/02-planner-contract.md)
- [Composite planner](02-composite.md)
- [Signal attention](../../04-sensing/01-signals.md)
- [Evaluation](../../06-evaluation/01-cases.md)
