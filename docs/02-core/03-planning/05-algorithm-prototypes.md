# Algorithm prototypes

These four prototypes turn the research directions in
[Algorithm directions](../../06-research/01-positioning/04-algorithm-directions.md) into runnable code.
They are deterministic, training-free and deliberately small. Each one is a first implementation, not
the full research method described in the memo.

| Prototype | API | Question |
|---|---|---|
| CA-VOD | `CAVODPlanner` | What is the value of acting, asking, waiting, verifying or escalating now? |
| AADS | `AttentionScheduler` | Which pending decision should receive scarce human attention? |
| CDR | `repair_continuity` | Which record should be revised when the decision history conflicts? |
| CDA | `counterfactual_attribution` | What is the smallest change that would flip the decision? |

## CA-VOD: commitment-attention value of decision

`CAVODPlanner` starts from the same four live terms as `LiveCompositePlanner` and adds:

- `information` for `ask`, `verify` and `observe`;
- `option` for `wait`.

The information value is `information_weight * uncertainty * information_gain`. The option value is
`waiting_weight * uncertainty`. The host can override either value in the option's `params`:

```python
from laix import ActionOption, CAVODPlanner, PlannerInput

plan = CAVODPlanner().solve(
    PlannerInput(
        subject="invoice 4832",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.6),
            ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
        ),
        attributes={"uncertainty": 0.8},
    )
)
print(plan.action_id, plan.attributes["information_value"])
```

`CAVODPlanner` implements the `Planner` protocol, so it works behind `PlannerPolicy`:

```python
from laix import CAVODPlanner, PlannerPolicy, decide

# request is the DecisionRequest built in the one-decision example.
decision = decide(request, policy=PlannerPolicy(CAVODPlanner(), name="ca_vod.v1"))[0]
```

The default path is one-step. Pass a `PomdpModel` and a belief to add a finite-horizon
belief-state future value without double-counting the immediate reward:

```python
from laix import CAVODPlanner, PomdpModel

planner = CAVODPlanner(
    pomdp_model=model,
    belief={"safe": 0.5, "risky": 0.5},
)
```

The future-value path uses the `action_future_value` helper from the POMDP planner. The full
constrained POMDP with hard commitment and attention constraints in the transition model remains
research work.

## AADS: attention-aware decision scheduling

`AttentionScheduler` ranks pending decisions with a Whittle-style index:

```text
index = (expected_gain * urgency - waiting_cost) / review_cost
```

The caller supplies risk, deadline, commitment flag, information value, waiting cost and review cost.
The scheduler allocates the attention budget in index order.

```python
from laix import AttentionCandidate, AttentionScheduler

schedule = AttentionScheduler().schedule(
    (
        AttentionCandidate(id="refund", risk=0.9, commitment=True, deadline="2026-11-01T10:05:00+00:00"),
        AttentionCandidate(id="routine", risk=0.2),
    ),
    now="2026-11-01T10:00:00+00:00",
    budget=1.0,
)
print([row.candidate_id for row in schedule.selected])
```

The full method is a restless multi-armed bandit. This prototype is a deterministic index policy.

## CDR: continuity decision repair

`repair_continuity` finds explicit conflicts and rule-derived conflicts in a decision history. It
supersedes the cheaper side of each conflict.

```python
from laix import ContinuityRecord, repair_continuity

plan = repair_continuity(
    (
        ContinuityRecord(id="approval-1", kind="approval", status="rejected", refs=("order-1",), cost=1.0),
        ContinuityRecord(id="receipt-1", kind="receipt", status="executed", refs=("order-1",), cost=3.0),
    )
)
print(plan.actions)
```

`consistent` reports whether the input history was already consistent; a plan with conflicts still
contains the actions that repair them. The full method is incremental truth maintenance with a
weighted MaxSAT repair. This prototype is a greedy minimum-cost repair.

## CDA: counterfactual decision attribution

`counterfactual_attribution` reads the component scores from a `Decision` produced by the live
composite or CA-VOD planner. For every alternative it computes the smallest single-component change
that would make the alternative overtake the chosen option.

```python
from laix import CAVODPlanner, PlannerPolicy, counterfactual_attribution, decide

# request is the DecisionRequest built in the one-decision example.
decision = decide(request, policy=PlannerPolicy(CAVODPlanner(), name="ca_vod.v1"))[0]
report = counterfactual_attribution(decision)
print(report.minimal.alternative_id, report.minimal.component, report.minimal.delta)
```

The full method handles rule-based and planning-based decisions with a search or MILP. This prototype
is exact for the additive composite score.

## Limits

- CA-VOD's future-value path is a finite-horizon belief lookahead; the constrained POMDP with hard
  commitment and attention constraints remains research.
- AADS is an index heuristic; it does not compute the exact Whittle index.
- CDR is greedy; it does not prove global minimum cost.
- CDA assumes an additive decision with component scores.

The next step for each is the research version described in
[Algorithm directions](../../06-research/01-positioning/04-algorithm-directions.md).
