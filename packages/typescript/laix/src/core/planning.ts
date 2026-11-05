export const COMMITMENT_STATUSES = ["open", "done", "cancelled"] as const;
export type CommitmentStatus = (typeof COMMITMENT_STATUSES)[number];

export interface Commitment {
  id: string;
  subject: string;
  due?: string | null;
  status?: CommitmentStatus;
  dependsOn?: string[];
  priority?: number;
  payload?: Record<string, unknown>;
}

function normalize(commitment: Commitment): Required<Commitment> {
  const status = commitment.status ?? "open";
  if (!COMMITMENT_STATUSES.includes(status)) {
    throw new Error(`unknown commitment status: ${status}`);
  }
  return {
    id: commitment.id,
    subject: commitment.subject,
    due: commitment.due ?? null,
    status,
    dependsOn: [...(commitment.dependsOn ?? [])],
    priority: commitment.priority ?? 0.5,
    payload: { ...(commitment.payload ?? {}) },
  };
}

export function commitmentDue(commitment: Commitment, now: Date): boolean {
  if (!commitment.due) return false;
  const due = Date.parse(commitment.due);
  return !Number.isNaN(due) && due <= now.getTime();
}

export class CommitmentLedger {
  private items = new Map<string, Required<Commitment>>();

  constructor(commitments: Commitment[] = []) {
    for (const commitment of commitments) {
      const item = normalize(commitment);
      this.items.set(item.id, item);
    }
  }

  add(commitment: Commitment): Required<Commitment> {
    const item = normalize(commitment);
    this.items.set(item.id, item);
    return item;
  }

  get(commitmentId: string): Required<Commitment> {
    const item = this.items.get(commitmentId);
    if (!item) throw new Error(`unknown commitment: ${commitmentId}`);
    return item;
  }

  complete(commitmentId: string): Required<Commitment> {
    return this.replace(commitmentId, "done");
  }

  cancel(commitmentId: string): Required<Commitment> {
    return this.replace(commitmentId, "cancelled");
  }

  open(): Required<Commitment>[] {
    return [...this.items.values()].filter((item) => item.status === "open");
  }

  due(now: Date): Required<Commitment>[] {
    return this.open().filter((item) => commitmentDue(item, now));
  }

  next(now: Date = new Date()): Required<Commitment> | null {
    const open = this.open();
    if (!open.length) return null;
    return this.first(open);
  }

  nextActionable(now: Date = new Date()): Required<Commitment> | null {
    const open = this.open().filter((item) => !this.blocked(item));
    if (!open.length) return null;
    return this.first(open);
  }

  blockedOpen(): Required<Commitment>[] {
    return this.open().filter((item) => this.blocked(item));
  }

  private first(items: Required<Commitment>[]): Required<Commitment> {
    return [...items].sort((left, right) => {
      const leftDue = left.due ? Date.parse(left.due) : Number.POSITIVE_INFINITY;
      const rightDue = right.due ? Date.parse(right.due) : Number.POSITIVE_INFINITY;
      const leftAt = Number.isNaN(leftDue) ? Number.POSITIVE_INFINITY : leftDue;
      const rightAt = Number.isNaN(rightDue) ? Number.POSITIVE_INFINITY : rightDue;
      if (leftAt !== rightAt) return leftAt - rightAt;
      if (left.priority !== right.priority) return right.priority - left.priority;
      return left.id < right.id ? -1 : left.id > right.id ? 1 : 0;
    })[0]!;
  }

  toDict(): { commitments: Commitment[] } {
    return {
      commitments: [...this.items.values()].map((item) => ({
        ...item,
        dependsOn: [...item.dependsOn],
        payload: { ...item.payload },
      })),
    };
  }

  static fromDict(payload: { commitments?: Commitment[] }): CommitmentLedger {
    return new CommitmentLedger([...(payload.commitments ?? [])]);
  }

  blocked(commitment: Commitment): boolean {
    for (const dependency of commitment.dependsOn ?? []) {
      const item = this.items.get(dependency);
      if (!item || item.status !== "done") return true;
    }
    return false;
  }

  private replace(commitmentId: string, status: CommitmentStatus): Required<Commitment> {
    const item = this.get(commitmentId);
    const updated: Required<Commitment> = { ...item, status };
    this.items.set(commitmentId, updated);
    return updated;
  }
}
