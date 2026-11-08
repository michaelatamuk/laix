# Single decision

A single-decision planner implements `Planner`: it receives one `PlannerInput` and returns one
`PlannerResult`.

| Page | Contents |
|---|---|
| [Planners](01-planners.md) | utility, commitment, execution-risk and human-attention planners |
| [Composite](02-composite.md) | `LiveCompositePlanner` and the combined score |
| [Model-based](03-model-based.md) | MDP and POMDP planners, value iteration and belief update |
| [Policies](04-policies.md) | `DecisionPolicy`, the registry and the packaged policies |
| [Decision value](05-decision-value.md) | CA-VOD information and option value |

The planner contract itself is in [Planner contract](../../01-contract/02-planner-contract.md).
