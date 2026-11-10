# Decision

The decision layer contains every algorithm that turns options and state into a choice. The code mirrors
that sentence:

```text
decision/planners/
  single/      # one live decision
  sequence/    # a finite chain of decisions
  fleet/       # many pending decisions competing for attention
  case_based/  # reuse of a similar decision
  history/     # a decision history that may need repair
  explain/     # why a decision happened, and what would flip it

decision/policies/   # the chooser layer
```

## The two planner protocols

- `Planner` answers one live decision: `solve(PlannerInput) -> PlannerResult`.
- `SequencePlanner` answers a chain: `plan(DecisionScenario) -> DecisionPlan`.

They are both decision planners, but they do not share a signature. The single-decision planners live
under `planners/single`; the sequence planners live under `planners/sequence`. That is why the docs keep them as
siblings, not as one folder inside the other.

## Read in order

1. [Single decision](01-single/README.md) — utility, commitments, execution risk, attention, CA-VOD,
   composite, MDP and POMDP planners, plus the single-decision extensions.
2. [Sequence](02-sequence/README.md) — CABB, rollout and replan.
3. [Fleet](03-fleet/README.md) — attention scheduling and the Whittle index.
4. [History](04-history/README.md) — decision continuity, repair and revalidation.
5. [Explain](05-explain/README.md) — counterfactual attribution, bounded search and decision counterfactuals.
6. [Policies](06-policies/README.md) — the chooser layer, packaged policies and wrappers.

The research results and the prior-art caveats are in
[Algorithm prototype results](../../07-research/02-evaluation/algorithm-prototypes.md).
