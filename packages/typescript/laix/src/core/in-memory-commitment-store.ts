import { CommitmentLedger, type Commitment } from "./planning.ts";
import type { CommitmentStore } from "./planning-store.ts";

export class InMemoryCommitmentStore implements CommitmentStore {
  private items = new Map<string, string>();

  save(key: string, ledger: CommitmentLedger): void {
    this.items.set(key, JSON.stringify(ledger.toDict()));
  }

  load(key: string): CommitmentLedger | null {
    const value = this.items.get(key);
    return value === undefined
      ? null
      : CommitmentLedger.fromDict(
          JSON.parse(value) as { commitments?: Commitment[] },
        );
  }

  delete(key: string): void {
    this.items.delete(key);
  }
}
