import type { StreamCheckpointStore } from "./checkpoint.ts";

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
