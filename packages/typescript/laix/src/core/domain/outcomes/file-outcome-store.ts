import type { Outcome } from "../../contracts.ts";
import { OutcomeLedger } from "./outcome-ledger.ts";

export interface OutcomeFiles {
  join(directory: string, name: string): string;
  read(path: string): string | null;
  write(path: string, text: string): void;
  remove(path: string): void;
}

export class FileOutcomeStore extends OutcomeLedger {
  readonly directory: string;
  readonly path: string;
  private readonly files: OutcomeFiles;

  constructor(directory: string, files: OutcomeFiles, filename = "outcomes.json") {
    super();
    this.directory = directory;
    this.files = files;
    this.path = files.join(directory, filename);
    const text = files.read(this.path);
    if (text !== null) {
      const payload = JSON.parse(text) as { outcomes?: Outcome[] };
      this.records = payload.outcomes ?? [];
    }
  }

  private flush(): void {
    this.files.write(
      this.path,
      JSON.stringify({ outcomes: this.records }, null, 2),
    );
  }

  override add(outcome: Outcome): Outcome {
    super.add(outcome);
    this.flush();
    return outcome;
  }
}
