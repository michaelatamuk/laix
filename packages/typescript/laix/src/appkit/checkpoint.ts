export interface StreamCheckpointStore {
  save(key: string, snapshot: Record<string, unknown>): void;
  load(key: string): Record<string, unknown> | null;
  delete(key: string): void;
}

export interface CheckpointFiles {
  join(directory: string, name: string): string;
  read(path: string): string | null;
  write(path: string, text: string): void;
  remove(path: string): void;
}

export class InMemoryStreamCheckpointStore implements StreamCheckpointStore {
  private items = new Map<string, string>();

  save(key: string, snapshot: Record<string, unknown>): void {
    this.items.set(key, JSON.stringify(snapshot));
  }

  load(key: string): Record<string, unknown> | null {
    const value = this.items.get(key);
    return value === undefined ? null : (JSON.parse(value) as Record<string, unknown>);
  }

  delete(key: string): void {
    this.items.delete(key);
  }
}

export class FileStreamCheckpointStore implements StreamCheckpointStore {
  readonly directory: string;
  private readonly files: CheckpointFiles;

  constructor(directory: string, files: CheckpointFiles) {
    this.directory = directory;
    this.files = files;
  }

  private path(key: string): string {
    const safe = key.replace(/[\\/:*?"<>|]/g, "_");
    return this.files.join(this.directory, `${safe}.json`);
  }

  save(key: string, snapshot: Record<string, unknown>): void {
    this.files.write(this.path(key), JSON.stringify(snapshot, null, 2));
  }

  load(key: string): Record<string, unknown> | null {
    const text = this.files.read(this.path(key));
    return text === null ? null : (JSON.parse(text) as Record<string, unknown>);
  }

  delete(key: string): void {
    this.files.remove(this.path(key));
  }
}
