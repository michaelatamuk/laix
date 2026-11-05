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

export { FileStreamCheckpointStore } from "./file-stream-checkpoint-store.ts";
export { InMemoryStreamCheckpointStore } from "./in-memory-stream-checkpoint-store.ts";
