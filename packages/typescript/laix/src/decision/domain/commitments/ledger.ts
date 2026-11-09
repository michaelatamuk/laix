import {
  commitmentDue,
  normalizeCommitment,
  type Commitment,
  type CommitmentStatus,
  type NormalizedCommitment,
} from "./commitment.ts";

export class CommitmentLedger {
  private items = new Map<string, NormalizedCommitment>();

  constructor(commitments: Commitment[] = []) {
    for (const commitment of commitments) {
      const item = normalizeCommitment(commitment);
      this.items.set(item.id, item);
    }
  }

  add(commitment: Commitment): NormalizedCommitment {
    const item = normalizeCommitment(commitment);
    this.items.set(item.id, item);
    return item;
  }

  get(commitmentId: string): NormalizedCommitment {
    const item = this.items.get(commitmentId);
    if (!item) throw new Error(`unknown commitment: ${commitmentId}`);
    return item;
  }

  complete(commitmentId: string): NormalizedCommitment {
    return this.replace(commitmentId, "done");
  }

  cancel(commitmentId: string): NormalizedCommitment {
    return this.replace(commitmentId, "cancelled");
  }

  all(): NormalizedCommitment[] {
    return [...this.items.values()];
  }

  open(): NormalizedCommitment[] {
    return [...this.items.values()].filter((item) => item.status === "open");
  }

  due(now: Date): NormalizedCommitment[] {
    return this.open().filter((item) => commitmentDue(item, now));
  }

  next(now: Date = new Date()): NormalizedCommitment | null {
    const open = this.open();
    if (!open.length) return null;
    return this.first(open);
  }

  nextActionable(now: Date = new Date()): NormalizedCommitment | null {
    const open = this.open().filter((item) => !this.blocked(item));
    if (!open.length) return null;
    return this.first(open);
  }

  blockedOpen(): NormalizedCommitment[] {
    return this.open().filter((item) => this.blocked(item));
  }

  private first(items: NormalizedCommitment[]): NormalizedCommitment {
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
        externalDependsOn: item.externalDependsOn.map((ref) => ({ ...ref })),
      })),
    };
  }

  static fromDict(payload: { commitments?: Commitment[] }): CommitmentLedger {
    return new CommitmentLedger([...(payload.commitments ?? [])]);
  }

  blocked(commitment: Commitment): boolean {
    // A local ledger cannot resolve another owner. Treat every external
    // reference as unresolved; use CommitmentGraph to resolve it.
    if ((commitment.externalDependsOn ?? []).length) return true;
    for (const dependency of commitment.dependsOn ?? []) {
      const item = this.items.get(dependency);
      if (!item || item.status !== "done") return true;
    }
    return false;
  }

  private replace(commitmentId: string, status: CommitmentStatus): NormalizedCommitment {
    const item = this.get(commitmentId);
    const updated: NormalizedCommitment = { ...item, status };
    this.items.set(commitmentId, updated);
    return updated;
  }
}
