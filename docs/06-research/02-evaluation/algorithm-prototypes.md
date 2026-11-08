# Algorithm prototype results

**Status:** prototype. These are deterministic smoke tests for the four algorithm directions, not
evidence of superiority. The cases are synthetic and few.

Reproduce:

```powershell
python scripts/novelty/bench/run_algorithm_bench.py
```

The raw output is in
[`results/algorithm-directions/summary.json`](../../../results/algorithm-directions/summary.json).

## CA-VOD against the live composite planner

Three synthetic cases exercise approval, uncertainty and the option to wait.

| Case | `LiveCompositePlanner` | `CAVODPlanner` | CA-VOD extra |
|---|---|---|---|
| Payment approval | `ask`, 1.09 | `ask`, 1.405 | information `0.315` |
| Uncertain verification | `act`, 0.5 | `verify`, 0.6375 | information `0.2375` |
| Wait option | `act`, 0.275 | `wait`, 0.325 | option value `0.225` |

The payment case chooses the same action but gives it a different score. The uncertain-verification
case flips from `act` to `verify`, and the wait case flips from `act` to `wait`. That is the intended
behaviour: CA-VOD prices information and the option to wait explicitly.

A separate belief-state case supplies a small `PomdpModel` and a 50/50 belief. The one-step path
chooses `act`; the belief-state path chooses `ask` with a future value of `0.45` because asking
reveals whether the state is safe or risky.

This is not a claim that CA-VOD is more accurate. It only shows that the new terms and the
belief-state future value change the choice in the cases designed to exercise them.

## AADS

Candidates: refund approval, routine review and evidence check. Budget: `1.5`.

- selected: `refund-approval`, `check-evidence`
- deferred: `routine-review`
- spent: `1.5`

The urgent, commitment-bearing review and the cheap information check win the budget. The routine
review waits.

The exact Whittle path uses a two-action arm. With `active_reward(bad)=1.0` the index is `0.9`; with
`active_reward(bad)=0.1` it is `0.09`. The higher-index arm is selected first. This is exact for the
single-arm model, not for the whole fleet.

## CDR

Records: an `approval` rejected for `order-1` and a `receipt` executed for `order-1`.

- conflict: `approval-1` / `receipt-1`
- action: supersede `approval-1`, cost `1.0`
- alternative cost: supersede `receipt-1`, cost `3.0`

The cheaper side is revised. This is a greedy minimum-cost repair, not a proof of global optimality.

A star-shaped conflict graph shows the difference. Greedy chooses the cheap leaves `a`, `c` and `d`
for a total cost of `3.0`; the exact minimum-weight vertex cover chooses `b` for a total cost of
`2.0`. Pass `exact=True` to use the branch-and-bound path.

## CDA

Decision: CA-VOD chooses `ask` on the payment case. The smallest single-component counterfactual is:

```text
wait overtakes ask if commitment increases by 0.970001
```

There are eight component-level counterfactuals because each alternative can flip through any of its
four components. The report ranks them by the required change.

The search path handles a rule-based decision. With `risk >= 0.5 -> escalate`, the base `risk=0.4`
chooses `act`; the smallest counterfactual is `risk=0.5`, distance `0.1`, result `escalate`.

## What the results do and do not show

They show:

- the prototypes are runnable and deterministic;
- CA-VOD can change the verb when information or option value is material;
- AADS allocates a budget in index order;
- CDR finds a conflict and repairs the cheaper side;
- CDA produces a ranked, minimal counterfactual.

They do not show:

- accuracy against a real baseline;
- superiority over `LiveCompositePlanner`, Rippletide or HazelJS;
- external validity;
- that the prototypes match the full research methods.

The next step is a larger benchmark with real cases, baselines and ablations, as described in
[Algorithm directions](../01-positioning/04-algorithm-directions.md).
