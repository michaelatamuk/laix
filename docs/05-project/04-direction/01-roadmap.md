# Roadmap

The planner roadmap is complete. Production depth has advanced: file-backed stores, execution retries,
async handlers, hard timeouts and OpenTelemetry attributes are done. External validation remains.
This page tracks what is done, what is next and what would count as a real step forward.

## Planners and composite planners

| Piece | Status |
|---|---|
| Rule policies | done |
| UCB bandit | done |
| Bench | done |
| Planner contract | done |
| `UtilityPlanner` | done |
| `CommitmentPlanner` | done |
| `ExecutionRiskPlanner` | done |
| `HumanAttentionPlanner` | done |
| `MDPPlanner` | done |
| Simulator and planner comparison | done |
| Planner bench CLI | done |
| Calibration | done |
| Model learning | done |
| `POMDPPlanner` | done |
| `LiveCompositePlanner` (composite planner) | done |
| `CAVODPlanner` (value of decision) | prototype |
| `AttentionScheduler` (AADS) | prototype; exact single-arm Whittle |
| `repair_continuity` (CDR) | prototype; exact small-graph repair |
| `counterfactual_attribution` (CDA) | prototype; linear and bounded search |
| TypeScript parity | done |
| Continuity benchmark | done |
| External validation | open |

## Production depth

| Piece | Status |
|---|---|
| Execution retries and capped backoff | done |
| Async execution handlers | done |
| Hard timeouts for async effects | done; a timeout returns `unknown` |
| File-backed state and outcome stores | done |
| OpenTelemetry decision attributes | done |
| LangGraph decision node, approval interrupt and checkpointer guide | done |
| MCP stdio server for `decide` | done |
| A2A 1.0 agent card and OpenAPI 3.1 action profile | done |
| Execution receipts, idempotency and reconciliation | done |
| Crash-recovery and retry semantics | tested for the bridge; host still owns worker recovery |

## Next

- Bootstrap intervals and covariate adjustment for causal effects.
- [MDP policy iteration](../../02-core/03-decision/01-single/03-model-based.md#mdp) as an alternative
  to value iteration.
- A generated API reference once the public surface is stable.
- An independent replication of the live and continuity results.
- One design partner with a measured before/after result.

The last two are adoption work, not feature work. See the [adoption plan](02-adoption-plan.md).

## Candidate planners

The current planners - utility, commitment, execution, attention, MDP and POMDP - are standard
methods. A differentiated planner can be built without training a model: it can plan over a model the
app supplies, enforce hard constraints and use state LAIX already carries.

| Candidate | What would be different | Training |
|---|---|---|
| **Risk-bounded planner** | Hard limits plus worst-case or CVaR guarantees, with an explanation. | none |
| **Case-based planner** | Reuse and adapt similar past decisions. | none |
| **Portfolio planner** | Choose which planner to run from the request shape and budget. | none |

A candidate counts as differentiated when it has:

1. a precise problem statement;
2. a benchmark against utility, commitment, execution, attention, MDP and POMDP on live tasks;
3. an explanation of why the result is different and durable.

A patent-level claim would also need a prior-art search.

The algorithm prototypes and the sequence family are in
[Algorithm prototypes](../../02-core/03-decision/README.md), with smoke results in
[Algorithm prototype results](../../06-research/02-evaluation/algorithm-prototypes.md).

## Research

The research tracks share one constraint: no model training or fine-tuning; planning runs over a
model the host supplies. External validation is the exception: it tests the results rather than
building a new planner.

| # | Track | Question | Status |
|---|---|---|---|
| 1 | Training-free live decisions | When are training-free decisions enough, and where do they fail? | done |
| 2 | Commitment-aware planning | Do promises, deadlines and dependencies change the optimal decision? | feature done |
| 3 | Execution-aware planning | Does modelling receipts, unknown outcomes and reversibility reduce irreversible errors? | feature done |
| 4 | Human approval and attention | Is human attention a scarce resource that planning should spend explicitly? | feature done |
| 5 | Decision-level calibration | Does calibrating the decision beat calibrating the prediction? | done |
| 6 | Streaming decision semantics | What are the correct semantics for decisions over event time, revisions and checkpoints? | done |
| 7 | Decision continuity | What changes when commitments, budget, approvals and revisions carry across a sequence of decisions? | done |
| 8 | External validation | Do the results hold in another environment, on another corpus, under another team? | open |
| 9 | CA-VOD | Does commitment- and attention-aware value of information beat the additive composite? | prototype |
| 10 | AADS | Does index scheduling improve attention use across a fleet of decisions? | prototype |
| 11 | CDR | Does minimum-cost continuity repair keep the decision history consistent? | prototype |
| 12 | CDA | Does counterfactual attribution explain a decision better than a score breakdown? | prototype |

A track becomes a paper with a precise problem, strong baselines (including published trained models
where relevant), ablations, reproducible code and honest limitations. The scope includes outcome
labels, calibration sets and causal inference; model training and fine-tuning remain a separate track.

## Limits

- A planner needs a world model. The app supplies transitions; LAIX plans over them.
- Utility elicitation remains the hard part.
- POMDPs get expensive quickly.
- Calibration needs real outcomes.
- Planner explanations are harder than rule traces.
- The live corpus is designed and maintained by the project.
- External validation is pending.
- Keep every piece optional.

## Related

- [Adoption plan](02-adoption-plan.md) - the market path.
- [Testing](../02-quality/01-testing.md) - how the claims are checked.
- [Evidence map](../../06-research/02-evaluation/evidence-map.md) - the scope of each result.
- [Versioning](../03-release/01-versioning.md) - release policy.
