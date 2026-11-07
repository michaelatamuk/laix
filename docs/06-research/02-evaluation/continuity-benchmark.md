# Decision-continuity benchmark

Status: synthetic mechanism test, v0. It is not external validation.

No public benchmark measures what happens when commitments, attention budget, approvals, revisions
and receipts carry from one decision to the next. This benchmark isolates that claim.

## Design

Twelve episodes, five decisions each. The corpus is
[`benchmarks/continuity/v1/episodes.json`](../../../benchmarks/continuity/v1/episodes.json).

Each episode carries:

- one open commitment with a due time;
- an attention budget;
- an approval state for the action;
- a receipt that becomes `unknown`, then `ok` or `failed`;
- the action history.

Three policies are compared:

| Policy | Sees |
|---|---|
| Reference | Full state; hand-written ground truth |
| Stateless | A static option set; no commitments, budget, approval or history |
| Stateful | Full state through `DecisionProblem.attributes` and `LiveDecisionEngine` |

The host asks for approval when a plan sets `requires_approval`.

## Result

| Policy | Success | Promise kept | Budget adhered | Approval correct | Continuity errors |
|---|---:|---:|---:|---:|---:|
| Reference | 100% | 100% | 100% | 100% | 0 |
| Stateless `UtilityEngine` | 0% | 100% | 0% | 100% | 36 |
| Stateful `LiveDecisionEngine` | 100% | 100% | 100% | 100% | 0 |

The stateless planner repeats the action because it cannot see that the commitment was fulfilled,
the attention budget was spent and the receipt was pending. The stateful runtime moves from approval
to action to verification.

## What it proves

It proves the **mechanism**: when the host supplies the state, `LiveDecisionEngine` uses it and a
stateless planner does not. It does not prove that real operators, real incidents or production
systems behave like the reference policy.

## Limitations

- Synthetic episodes and a designed action space.
- Hand-written reference policy.
- Revisions, dependencies and multi-step recovery are not in v0.
- Twelve episodes and one deterministic run; no variance estimate.
- Approval is modelled through the plan flag and a host rule, not a real approval queue.

## Next

- Add revision events and blocked dependencies.
- Add failed execution and recovery paths.
- Run the same episodes with JEV or an LLM as the chooser and LAIX as the guardrail.
- Replace the synthetic episodes with recorded incident sequences when data exists.

See [`results/continuity-benchmark/`](../../../results/continuity-benchmark/README.md) and
[`benchmarks/continuity/v1/`](../../../benchmarks/continuity/v1/README.md).
