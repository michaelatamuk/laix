import type { CommitmentLedger } from "./commitments.ts";

export interface CommitmentStore {
  save(key: string, ledger: CommitmentLedger): void;
  load(key: string): CommitmentLedger | null;
  delete(key: string): void;
}

export interface CommitmentFiles {
  join(directory: string, name: string): string;
  read(path: string): string | null;
  write(path: string, text: string): void;
  remove(path: string): void;
}

export { FileCommitmentStore } from "./file-commitment-store.ts";
export { InMemoryCommitmentStore } from "./in-memory-commitment-store.ts";
