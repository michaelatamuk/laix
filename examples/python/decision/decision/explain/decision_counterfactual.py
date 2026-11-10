"""Show which verification would flip a commitment decision."""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    CommitmentGraph,
    CommitmentLedger,
    CommitmentPlanner,
    CommitmentRef,
    PlannerInput,
    commitment_verification_counterfactual,
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

result = commitment_verification_counterfactual(problem, CommitmentPlanner())
flip = result.flips[0]

print(result.base_action_id, flip.name, flip.counterfactual_action_id)
