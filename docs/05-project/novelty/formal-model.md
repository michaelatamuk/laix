# Formal model and invariants

Define the contribution precisely and test the properties the paper will claim.

## 1. Formal contribution

### Deliverable

This page should contain the decision problem, scoring composition, feasibility rules and state
transitions. Add property tests that fail if an invariant is broken.

### Definitions to write down

- `DecisionProblem`: subject, time, situation, options, signals, context, attributes.
- `ActionOption`: verb, benefit, cost, risk, latency, interruption, reversibility,
  approval, execution facts, commitment effects.
- `Commitment`: id, subject, due time, status, dependencies, priority.
- `AttentionBudget`: total, spent, remaining.
- `ExecutionReceipt`: status, actor, approval, idempotency key, detail, previous state.
- `Plan`: chosen verb/action, confidence, score, alternatives, attributes.
- `Decision`: public contract derived from a plan.
- `Revision`: revision number, predecessor, event time, stream id, status.
- `Timeline`: append-only set with revision rules.

### Score composition

Document the actual formula used by `LiveDecisionEngine`:

```text
total = utility + commitment + execution + attention
```

For each term, define:

- inputs;
- weights and defaults;
- feasibility gates;
- tie-breaking;
- why a term can veto an option;
- what happens when a term is unknown.

### Invariants

Write tests for at least these:

1. The same problem and configuration produce the same plan.
2. A hard constraint cannot be outscored by a high utility.
3. Attention spent never exceeds the budget and never becomes negative.
4. A rejected approval cannot be selected.
5. A higher revision always has a predecessor and never moves event time backwards.
6. A receipt follows a valid state machine:
   `pending -> approved -> executed -> undone`, with `unknown`, `failed`, `refused`,
   `cancelled` handled explicitly.
7. A decision trace is append-only.
8. Calibration never produces a confidence outside `[0, 1]`.
9. Simulation and live planning use the same contract conversion.
10. Python and TypeScript produce the same decision for shared cases.

### Acceptance criteria

- Every invariant has a test that would fail if the code regressed.
- The document explains the contribution without relying on code comments.
- The formulas match the implementation.
