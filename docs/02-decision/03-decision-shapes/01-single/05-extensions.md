# Single-decision extensions

These planners extend the single-decision layer without adding a data product. Each one answers a
decision question: which planner to use, whether the downside is acceptable, what to verify, or which
conflict response to choose.

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
The composite, CA-VOD and CABB sequence planners accept the same `require_verified` and
`max_verification_age` settings, so cross-owner blockers reach the whole decision stack.

## Belief-aware planning

`CommitmentBeliefPlanner` weights expected utility by the chance that external dependencies complete.
The probability comes from `attributes["commitment_probabilities"]` (keyed by `owner/ledger/id`,
`owner:id` or plain id), then from `payload["completion_probability"]`, then from
`default_probability`. Trusted and fresh verified promises count as certain.

If the best action's completion probability is below `verify_below`, the planner returns `verify`
with the uncertain references instead of acting on a low-confidence promise.

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

## Elsewhere

- Decision revalidation is in [History](../04-history/03-revalidation.md).
- Decision counterfactuals are in [Explain](../05-explain/03-counterfactual.md).
- Policy iteration is in [Model-based](03-model-based.md#policy-iteration).

## Related

- [Single decision planners](01-planners.md)
- [Composite](02-composite.md)
- [Model-based](03-model-based.md)
- [Policies](../06-policies/README.md)
- [Commitments](../../02-domain/02-commitments.md)
