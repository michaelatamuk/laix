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

| Page | Contents |
|---|---|
| [Policy contract](01-policy-contract.md) | `DecisionPolicy`, registry, built-in action policy and the planner bridge |
| [Packaged policies](02-packaged-policies.md) | the eight decision classes, rules, wrappers and the bandit policy |

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
