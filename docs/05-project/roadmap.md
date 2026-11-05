# Roadmap

The planner and production-depth roadmap is complete. This page tracks what is done and what is
still open.

## Planners

| Piece | Status |
|---|---|
| Rule policies | done |
| UCB bandit | done |
| Bench | done |
| Planner contract | done |
| Utility planner | done |
| Commitment-aware planner | done |
| Execution-aware planner | done |
| Attention-aware planner | done |
| Integrated live planner | done |
| MDP planner | done |
| Simulator and planner comparison | done |
| Planner bench CLI | done |
| Calibration | done |
| Model learning | done |
| POMDP | done |
| TypeScript parity | done |

## Build order

1. Planner contract — `DecisionProblem`, `Plan`, `DecisionEngine`, `EnginePolicy`, `to_problem` and
   `to_decision`.
2. Utility and constraint planner — expected utility, hard constraints, risk attitude, explanation.
3. MDP planner — [states, actions, transitions](../02-core/06-engines.md#what-an-mdp-is), discount,
   horizon, optimality gap.
4. Simulator and bench — deterministic and seeded stochastic rollouts, comparison and regression.
5. Calibration — predicted vs observed confidence, per-policy reports, adjustment.
6. Model learning — transitions and rewards, rollback, export as an `MdpModel`.
7. POMDP — observation model, belief update, small solver, comparison with the MDP path.
8. TypeScript parity — contract, utility, MDP, POMDP, calibration, model learning and simulator.

## Next

- Execution retries, backoff and timeouts around `ExecutionBridge`.
- Async execution handlers alongside the current synchronous handlers.
- Bootstrap intervals and covariate adjustment for causal effects.
- [MDP policy iteration](../02-core/06-engines.md#what-an-mdp-is) as an alternative to value iteration.
- File-backed state and outcome stores for hosts that want an adapter out of the box.
- Generated API reference once the public surface is stable.

## Candidate planners

The current planners — Utility, MDP and POMDP — are standard methods. A differentiated planner can
be built without training a model: it can plan over a model the app supplies, enforce hard
constraints and use state LAIX already carries.

| Candidate | What would be different | Training |
|---|---|---|
| **Deadline and attention planner** | timing and attention are actions in the same plan | none |
| **Commitment-aware planner** | promises, due times and dependencies are part of the state | none |
| **Execution-aware planner** | receipts, unknown outcomes, reversibility and undo cost are part of the state | none |
| **Risk-bounded planner** | hard limits plus worst-case or CVaR guarantees, with an explanation | none |
| **Case-based planner** | reuse and adapt similar past decisions | none |

The strongest fit is the commitment/execution-aware planner: commitments, receipts, idempotency,
recovery and outcomes already exist in the app kit.

A candidate counts as differentiated when it has:

1. a precise problem statement;
2. a benchmark against Utility, MDP and POMDP on live tasks;
3. an explanation of why the result is different and durable.

A patent-level claim would also need a prior-art search.

## Research

Six training-free tracks could become papers once built and evaluated. They share one constraint:
no model training or fine-tuning; planning runs over a model the host supplies.

| # | Track | Question | Status |
|---|---|---|---|
| 1 | Training-free live decisions | When are training-free decisions enough, and where do they fail? | done |
| 2 | Commitment-aware planning | Do promises, deadlines and dependencies change the optimal decision? | feature done |
| 3 | Execution-aware planning | Does modelling receipts, unknown outcomes and reversibility reduce irreversible errors? | feature done |
| 4 | Human approval and attention | Is human attention a scarce resource that planning should spend explicitly? | feature done |
| 5 | Decision-level calibration | Does calibrating the decision beat calibrating the prediction? | done |
| 6 | Streaming decision semantics | What are the correct semantics for decisions over event time, revisions and checkpoints? | done |

A track becomes a paper with a precise problem, strong baselines (including published trained
models where relevant), ablations, reproducible code, and honest limitations. The scope includes
outcome labels, calibration sets and causal inference; model training and fine-tuning remain a
separate track.

## Limits

- A planner needs a world model. The app supplies transitions; LAIX plans over them.
- Utility elicitation remains the hard part.
- POMDPs get expensive quickly.
- Calibration needs real outcomes.
- Planner explanations are harder than rule traces.
- Keep every piece optional.
