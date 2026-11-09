export const COMMITMENT_STATUSES = ["open", "done", "cancelled"] as const;
export type CommitmentStatus = (typeof COMMITMENT_STATUSES)[number];

export const COMMITMENT_SOURCES = ["local", "reported", "verified"] as const;
export type CommitmentSource = (typeof COMMITMENT_SOURCES)[number];

export interface CommitmentRef {
  owner: string;
  id: string;
  ledger?: string | null;
}

export interface Commitment {
  id: string;
  subject: string;
  due?: string | null;
  status?: CommitmentStatus;
  dependsOn?: string[];
  priority?: number;
  payload?: Record<string, unknown>;
  owner?: string;
  ledger?: string | null;
  source?: CommitmentSource;
  verifiedAt?: string | null;
  externalDependsOn?: CommitmentRef[];
}

export interface NormalizedCommitment extends Commitment {
  due: string | null;
  status: CommitmentStatus;
  dependsOn: string[];
  priority: number;
  payload: Record<string, unknown>;
  owner: string;
  ledger: string | null;
  source: CommitmentSource;
  verifiedAt: string | null;
  externalDependsOn: CommitmentRef[];
}

export function commitmentKey(ref: CommitmentRef): string {
  return `${ref.owner}\u0000${ref.ledger ?? ""}\u0000${ref.id}`;
}

export function commitmentRef(commitment: Commitment): CommitmentRef {
  return {
    owner: commitment.owner ?? "local",
    ledger: commitment.ledger ?? null,
    id: commitment.id,
  };
}

export function normalizeCommitment(commitment: Commitment): NormalizedCommitment {
  const status = commitment.status ?? "open";
  if (!COMMITMENT_STATUSES.includes(status)) {
    throw new Error(`unknown commitment status: ${status}`);
  }
  const source = commitment.source ?? "local";
  if (!COMMITMENT_SOURCES.includes(source)) {
    throw new Error(`unknown commitment source: ${source}`);
  }
  const owner = commitment.owner ?? "local";
  if (!owner) throw new Error("commitment owner must not be empty");
  return {
    id: commitment.id,
    subject: commitment.subject,
    due: commitment.due ?? null,
    status,
    dependsOn: [...(commitment.dependsOn ?? [])],
    priority: commitment.priority ?? 0.5,
    payload: { ...(commitment.payload ?? {}) },
    owner,
    ledger: commitment.ledger ?? null,
    source,
    verifiedAt: commitment.verifiedAt ?? null,
    externalDependsOn: [...(commitment.externalDependsOn ?? [])].map((ref) => ({ ...ref })),
  };
}

export function commitmentDue(commitment: Commitment, now: Date): boolean {
  if (!commitment.due) return false;
  const due = Date.parse(commitment.due);
  return !Number.isNaN(due) && due <= now.getTime();
}

export function commitmentTrusted(commitment: Commitment): boolean {
  const source = commitment.source ?? "local";
  return source !== "reported";
}
