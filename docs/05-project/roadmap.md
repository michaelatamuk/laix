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

## Limits

- A planner needs a world model. The app supplies transitions; LAIX plans over them.
- Utility elicitation remains the hard part.
- POMDPs get expensive quickly.
- Calibration needs real outcomes.
- Planner explanations are harder than rule traces.
- Keep every piece optional.
