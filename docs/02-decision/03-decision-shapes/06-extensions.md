# Planner extensions

These planners extend the decision layer without adding a data product. Each one answers a decision
question: which planner to use, whether the downside is acceptable, what to verify, whether an old
decision still holds, or which conflict response to choose.

## Planner selection

`PortfolioPlanner` chooses a named planner from a portfolio.

```python
portfolio = PortfolioPlanner(
    {
        "utility": UtilityPlanner(),
        "commitment": CommitmentPlanner(),
        "execution": ExecutionRiskPlanner(),
    },
    default="utility",
)
```

The default selector reads `attributes["planner"]` first, then inspects commitments, approvals,
risk, attention and model attributes. The result carries `planner` and `portfolio` in its
attributes. A host can pass its own selector when it has a better rule.

## Risk-bounded planning

`RiskBoundedPlanner` rejects options whose downside exceeds a hard limit.

```python
ActionOption(
    id="deploy",
    verb="act",
    name="deploy",
    params={"risk_bound": {"worst_case_loss": 0.8, "cvar_loss": 0.4}},
)
```

The planner reads `risk_bound` or `risk`, uses `worst_case_loss` and `cvar_loss` (falling back to the
option's `risk`), and rejects an option when CVaR exceeds `max_loss`. The result reports
`risk_limit`, `worst_case_loss` and `cvar_loss`; alternatives use `risk_limit` or
`lower_risk_adjusted_score`.

## Commitment resolution

`CommitmentResolutionPlanner` runs the commitment planner and, when the best it can do is `wait`
because of blocked commitments, returns a concrete next step:

- `verify` with `intent.capability="verify_commitment"` by default,
- `ask` when constructed with `mode="ask"`.

The result carries `verification_refs` and `blocked_by`, each with `{owner, ledger, id, reason}`.

## Decision revalidation

`RevalidationPlanner` wraps another planner and compares the new result with a previous decision.

| Result | Reason code | Meaning |
|---|---|---|
| `wait` | `decision_held` | the previous action is still the best |
| current verb | `decision_revised` | a different action is now best |
| `escalate` | `decision_escalated` | the previous action is no longer feasible |

The previous action comes from `attributes["previous_decision"]` or
`attributes["previous_action_id"]`.

## Case-based planning

`CaseBasedPlanner` reuses a similar past decision.

```python
CaseBasedPlanner(
    (PastDecision(subject="send the report", action_id="send-now"),),
)
```

Similarity combines subject-token overlap with whether the past action is still available. If
nothing clears the threshold, the planner uses a fallback or returns `wait` with `no_case`.

## Goal and constraint conflicts

`ConflictResolutionPlanner` reads explicit conflicts from `attributes["goal_conflicts"]`. An option
may declare `params["resolves"]` with conflict ids. If no option resolves them, the planner returns
`ask` or `escalate` based on severity. With no conflict, it delegates to its wrapped planner.

## Policy iteration

`policy_iteration` solves a discounted infinite-horizon `MdpModel` and returns a stationary policy,
values and iteration count. It complements `value_iteration`; finite-horizon models should keep using
value iteration because their policy is time-dependent.

## Counterfactual decisions

`decision_counterfactual` solves a base problem and named candidate problems, then reports which
candidate changes the action. `commitment_verification_counterfactual` applies the same idea to
external commitments: it marks one external promise verified at a time and reports the verification
that would flip the decision.

## Commitment rejection codes

`CommitmentPlanner` alternatives carry `rejected_reason_code`:

```text
blocked_hard_commitment
blocked_missing_dependency
blocked_stale_dependency
blocked_unverified_dependency
blocked_open_dependency
outside_hard_limits
lower_commitment_score
```

Use the code for branching and `rejected_because` for display.

## Related

- [Single decision planners](01-single/01-planners.md)
- [History](04-history.md)
- [Explain](05-explain.md)
- [Commitments](../02-domain/02-commitments.md)
