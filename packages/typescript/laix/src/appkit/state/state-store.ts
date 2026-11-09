import { ExperienceState } from "./state.ts";

export interface StateStore {
  save(key: string, state: ExperienceState): void;
  load(key: string): ExperienceState | null;
  delete(key: string): void;
}

export interface StateFiles {
  join(directory: string, name: string): string;
  read(path: string): string | null;
  write(path: string, text: string): void;
  remove(path: string): void;
}

export class InMemoryStateStore implements StateStore {
  private items = new Map<string, ExperienceState>();

  save(key: string, state: ExperienceState): void {
    this.items.set(key, state);
  }

  load(key: string): ExperienceState | null {
    return this.items.get(key) ?? null;
  }

  delete(key: string): void {
    this.items.delete(key);
  }
}

export class FileStateStore implements StateStore {
  readonly directory: string;
  private readonly files: StateFiles;

  constructor(directory: string, files: StateFiles) {
    this.directory = directory;
    this.files = files;
  }

  private path(key: string): string {
    const safe = key.replace(/[\\/:*?"<>|]/g, "_");
    return this.files.join(this.directory, `${safe}.json`);
  }

  save(key: string, state: ExperienceState): void {
    this.files.write(this.path(key), JSON.stringify(state.snapshot(), null, 2));
  }

  load(key: string): ExperienceState | null {
    const text = this.files.read(this.path(key));
    return text === null ? null : ExperienceState.fromSnapshot(JSON.parse(text));
  }

  delete(key: string): void {
    this.files.remove(this.path(key));
  }
}
