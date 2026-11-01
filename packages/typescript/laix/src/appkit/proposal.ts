export const PROPOSAL_STATUSES = ["pending", "approved", "rejected", "applied", "undone"] as const;
export type ProposalStatus = (typeof PROPOSAL_STATUSES)[number];

export interface Proposal {
  id: string;
  title: string;
  summary: string;
  decisionId?: string;
  actionId?: string | null;
  status?: ProposalStatus;
  createdAt?: string;
  createdBy?: string;
  approvedBy?: string | null;
  approvedAt?: string | null;
  appliedAt?: string | null;
  undoHint?: string | null;
  payload?: Record<string, unknown>;
}

function copy(proposal: Proposal, changes: Partial<Proposal>): Proposal {
  return { ...proposal, ...changes };
}

function statusOf(proposal: Proposal): ProposalStatus {
  return proposal.status ?? "pending";
}

export function createProposal(proposal: Proposal): Proposal {
  return copy(proposal, { status: statusOf(proposal), createdAt: proposal.createdAt ?? new Date().toISOString(), createdBy: proposal.createdBy ?? "agent" });
}

export function approveProposal(proposal: Proposal, by: string, at?: string): Proposal {
  if (statusOf(proposal) !== "pending") throw new Error(`cannot approve a ${statusOf(proposal)} proposal`);
  return copy(proposal, { status: "approved", approvedBy: by, approvedAt: at ?? new Date().toISOString() });
}

export function rejectProposal(proposal: Proposal, by: string, at?: string): Proposal {
  if (statusOf(proposal) !== "pending") throw new Error(`cannot reject a ${statusOf(proposal)} proposal`);
  return copy(proposal, { status: "rejected", approvedBy: by, approvedAt: at ?? new Date().toISOString() });
}

export function applyProposal(proposal: Proposal, at?: string): Proposal {
  if (statusOf(proposal) !== "approved") throw new Error(`cannot apply a ${statusOf(proposal)} proposal`);
  return copy(proposal, { status: "applied", appliedAt: at ?? new Date().toISOString() });
}

export function undoProposal(proposal: Proposal, at?: string): Proposal {
  if (statusOf(proposal) !== "applied") throw new Error(`cannot undo a ${statusOf(proposal)} proposal`);
  return copy(proposal, { status: "undone", appliedAt: at ?? new Date().toISOString() });
}
