import { CommitmentLedger } from "./commitments.ts";
import type { CommitmentFiles, CommitmentStore } from "./store.ts";

export class FileCommitmentStore implements CommitmentStore {
  readonly directory: string;
  private readonly files: CommitmentFiles;

  constructor(directory: string, files: CommitmentFiles) {
    this.directory = directory;
    this.files = files;
  }

  private path(key: string): string {
    const safe = key.replace(/[\\/:*?"<>|]/g, "_");
    return this.files.join(this.directory, `${safe}.json`);
  }

  save(key: string, ledger: CommitmentLedger): void {
    this.files.write(this.path(key), JSON.stringify(ledger.toDict(), null, 2));
  }

  load(key: string): CommitmentLedger | null {
    const text = this.files.read(this.path(key));
    return text === null ? null : CommitmentLedger.fromDict(JSON.parse(text));
  }

  delete(key: string): void {
    this.files.remove(this.path(key));
  }
}
