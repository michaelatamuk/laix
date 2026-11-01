import type { ExperienceState } from "./state.ts";

export interface StateStore {
  save(key: string, state: ExperienceState): void;
  load(key: string): ExperienceState | null;
  delete(key: string): void;
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
