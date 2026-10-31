"""A proposed action needs a person. Move it through the lifecycle.

The result is:

    pending approved applied undone

- pending: the proposal is waiting for a person.
- approved: a person allowed it.
- applied: the host performed it.
- undone: the host reversed it.
"""

from laix import Proposal, apply_proposal, approve_proposal, undo_proposal

proposal = Proposal(
    id="p-1",
    title="Change the delivery window",
    summary="Move Friday's delivery to Saturday morning.",
    decision_id="d-1",
)
approved = approve_proposal(proposal, by="owner")
applied = apply_proposal(approved)
undone = undo_proposal(applied)

print(proposal.status, approved.status, applied.status, undone.status)
