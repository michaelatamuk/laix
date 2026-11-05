/** A proposed action needs a person. Move it through the lifecycle. */
import {
  applyProposal,
  approveProposal,
  createProposal,
  undoProposal,
} from "../../../packages/typescript/laix/src/index.ts";

const proposal = createProposal({ id: "p-1", title: "Change the delivery window", summary: "Move Friday to Saturday." });
const approved = approveProposal(proposal, "owner");
const applied = applyProposal(approved);
const undone = undoProposal(applied);
console.log(proposal.status, approved.status, applied.status, undone.status);
