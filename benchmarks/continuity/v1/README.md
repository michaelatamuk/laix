# Decision-continuity benchmark v0

Status: synthetic mechanism test. Not a generalisation claim.

This corpus tests whether a decision runtime carries state from one decision into the next. A
stateless utility planner sees a fixed option set and no episode state. `LiveDecisionEngine` sees
the open commitment, attention budget, approval state and execution receipt.

## Episode

Each episode is five decisions:

1. approval is requested;
2. the action fulfils the commitment;
3. the receipt is verified;
4. a failed receipt escalates, otherwise the episode waits;
5. the episode settles.

State that evolves:

- one open commitment with a due time;
- an attention budget;
- an approval state for the action;
- a receipt that becomes `unknown`, then `ok` or `failed`;
- the action history.

`episodes.json` is the versioned corpus. Each row has `id`, `due_step`, `receipt_outcome`,
`budget_total` and `steps`.

## Policies

- **Reference:** a hand-written deterministic policy that uses the full state. It is the ground
  truth.
- **Stateless:** `UtilityPlanner` on a static option set. It never sees commitments, attention,
  approval or prior actions.
- **Stateful:** `LiveDecisionEngine` with the commitment, `AttentionBudget`, approval map and
  execution state in `DecisionProblem.attributes`. The host asks for approval when the plan sets
  `requires_approval`.

## Metrics

- episode success;
- promise kept;
- attention budget adhered;
- approval correct;
- continuity errors (duplicate actions after the commitment was already fulfilled).

## Run

```bash
python scripts/novelty/continuity/run_continuity_bench.py
```

The summary is written to `results/continuity-benchmark/metrics/summary.json`.

## Limitations

- Synthetic episodes with a designed action space.
- The reference policy is hand-written.
- The stateful result shows that the runtime uses the supplied state; it does not prove that real
  operators or real incidents behave the same way.
- Revisions, dependencies and multi-step recovery are not in v0.
