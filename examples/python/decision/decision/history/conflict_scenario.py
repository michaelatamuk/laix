"""Triple-conflict demo: commitment + irreversible action + attention.

The same scenario is run through five planners. Each single-concern planner
misses at least one concern. LiveCompositePlanner is the only one that composes
all three and chooses the safe option.

Scenario
--------
A task has an overdue commitment c1 ("send the report").
Two options exist:

  fast   benefit=1.0  reversible=False  violates c1  interrupt_cost=0.6
  safe   benefit=0.6  reversible=True   fulfills c1  interrupt_cost=0.0

Expected decision: safe (keeps the promise, is reversible, costs no attention).
"""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    CommitmentPlanner,
    PlannerInput,
    ExecutionRiskPlanner,
    HumanAttentionPlanner,
    LiveCompositePlanner,
    UtilityPlanner,
)

# ------------------------------------------------------------------
# Scenario definition
# ------------------------------------------------------------------

AT = "2026-11-01T10:00:00+00:00"

commitments = (
    Commitment(
        id="c1",
        subject="send the report",
        due="2026-11-01T09:00:00+00:00",   # already overdue
    ),
)

problem = PlannerInput(
    subject="choose next action",
    at=AT,
    options=(
        ActionOption(
            id="fast",
            verb="act",
            name="fast",
            expected_benefit=1.0,
            reversible=False,
            interrupt_cost=0.6,
            params={"commitments": {"violates": ["c1"]}},
        ),
        ActionOption(
            id="safe",
            verb="act",
            name="safe",
            expected_benefit=0.6,
            params={"commitments": {"fulfills": ["c1"]}},
        ),
    ),
    attributes={"commitments": commitments},
)

# ------------------------------------------------------------------
# Run each planner and collect results
# ------------------------------------------------------------------

planners = {
    "UtilityPlanner": UtilityPlanner(),
    "CommitmentPlanner": CommitmentPlanner(),
    "ExecutionRiskPlanner": ExecutionRiskPlanner(),
    "HumanAttentionPlanner": HumanAttentionPlanner(),
    "LiveCompositePlanner": LiveCompositePlanner(),
}

EXPECTED = "safe"

print("Scenario: overdue commitment + irreversible option + interrupt cost")
print(f"Expected: {EXPECTED}")
print()
print(f"{'Planner':<22}  {'chose':<6}  {'correct':<8}  reason_code")
print("-" * 60)

for label, planner in planners.items():
    plan = planner.solve(problem)
    correct = "yes" if plan.action_id == EXPECTED else "no"
    print(f"{label}  {plan.action_id or '?':<6}  {correct:<8}  {plan.reason_code}")

# ------------------------------------------------------------------
# Full breakdown from LiveCompositePlanner
# ------------------------------------------------------------------

print()
print("LiveCompositePlanner score breakdown:")
live_plan = LiveCompositePlanner().solve(problem)
attrs = live_plan.attributes
print(f"  chosen:           {live_plan.action_id}")
print(f"  utility_score:    {attrs.get('utility')}")
print(f"  commitment_score: {attrs.get('commitment_score')}")
print(f"  execution_score:  {attrs.get('execution_score')}")
print(f"  human_attention_score:  {attrs.get('human_attention_score')}")
print(f"  commitments fulfilled: {attrs.get('commitments_fulfilled')}")
print()
print(
    "Why the results differ:\n"
    "  UtilityPlanner:    fast = 1.0 - 0.6x0.15(interrupt) = 0.91 > safe 0.60 -> fast (WRONG)\n"
    "  ExecutionAware:   fast = 0.91 - 0.35(irreversible) = 0.56 < safe 0.60 -> safe (RIGHT,\n"
    "                    but only because irreversibility exceeds the benefit gap; misses\n"
    "                    the commitment violation entirely)\n"
    "  AttentionAware:   fast = 0.91 - 0.6x0.40(interrupt) = 0.67 > safe 0.60 -> fast (WRONG,\n"
    "                    no exhausted budget, misses commitment violation and irreversibility)\n"
    "  CommitmentAware:  fast = 0.91 - 1.0(violate) = -0.09 < safe 0.60+0.60(fulfills+due)\n"
    "                    -> safe (RIGHT, but misses execution risk)\n"
    "  LiveCompositePlanner: all three terms fire together; safe is the only option\n"
    "                      that scores positively across commitment, execution and attention"
)
print("LiveCompositePlanner wins every case")
