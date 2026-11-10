"""Turn a blocked or uncertain external promise into a verification decision."""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    CommitmentBeliefPlanner,
    CommitmentGraph,
    CommitmentLedger,
    CommitmentRef,
    CommitmentResolutionPlanner,
    PlannerInput,
)

supplier = CommitmentRef(owner="supplier", ledger="supplier", id="ship")
local = CommitmentLedger(
    (
        Commitment(
            id="deliver",
            subject="deliver the order",
            external_depends_on=(supplier,),
        ),
    )
)
external = Commitment(
    id="ship",
    subject="ship the part",
    owner="supplier",
    ledger="supplier",
    status="done",
    source="reported",
)
problem = PlannerInput(
    subject="deliver",
    at="2026-11-01T10:00:00+00:00",
    options=(
        ActionOption(
            id="finish",
            verb="act",
            name="finish the delivery",
            expected_benefit=1.0,
            params={"commitments": {"fulfills": ["deliver"], "hard": True}},
        ),
        ActionOption(
            id="wait",
            verb="wait",
            name="wait for verification",
            expected_benefit=0.1,
        ),
    ),
    attributes={"commitment_graph": CommitmentGraph(local, (external,))},
)

resolution = CommitmentResolutionPlanner().solve(problem)
belief = CommitmentBeliefPlanner(default_probability=0.4).solve(problem)

print(resolution.verb, resolution.reason_code)
print(belief.verb, belief.attributes["completion_probability"])
