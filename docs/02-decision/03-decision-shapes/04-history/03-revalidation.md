# Revalidation

`RevalidationPlanner` wraps another planner and compares the new result with a previous decision.

| Result | Reason code | Meaning |
|---|---|---|
| `wait` | `decision_held` | the previous action is still the best |
| current verb | `decision_revised` | a different action is now best |
| `escalate` | `decision_escalated` | the previous action is no longer feasible |

The previous action comes from `attributes["previous_decision"]` or
`attributes["previous_action_id"]`.

## Related

- [History overview](README.md)
- [Continuity](01-continuity.md)
- [Repair](02-repair.md)
