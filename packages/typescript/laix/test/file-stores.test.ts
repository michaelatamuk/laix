import assert from "node:assert/strict";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  ExperienceState,
  FileOutcomeStore,
  FileStateStore,
} from "../src/index.ts";
import type { Outcome, StateFiles } from "../src/index.ts";

const files: StateFiles = {
  join: (directory, name) => join(directory, name),
  read: (path) => (existsSync(path) ? readFileSync(path, "utf8") : null),
  write: (path, text) => writeFileSync(path, text, "utf8"),
  remove: (path) => {
    if (existsSync(path)) unlinkSync(path);
  },
};

describe("file stores", () => {
  it("round-trips experience state", () => {
    const directory = mkdtempSync(join(tmpdir(), "laix-state-"));
    mkdirSync(directory, { recursive: true });
    try {
      const store = new FileStateStore(directory, files);
      const state = new ExperienceState("one", "decide");
      state.beliefs.set("goal", {
        id: "goal",
        proposition: "the goal is reachable",
        confidence: 0.7,
      });
      store.save("show/1", state);

      const loaded = store.load("show/1");
      assert.equal(loaded?.subject, "one");
      assert.equal(loaded?.phase, "decide");
      assert.equal(loaded?.beliefs.get("goal")?.confidence, 0.7);

      store.delete("show/1");
      assert.equal(store.load("show/1"), null);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  it("round-trips outcomes", () => {
    const directory = mkdtempSync(join(tmpdir(), "laix-outcomes-"));
    mkdirSync(directory, { recursive: true });
    try {
      const store = new FileOutcomeStore(directory, files);
      const outcome: Outcome = {
        id: "o-1",
        decisionId: "d-1",
        metric: "time",
        before: 10,
        after: 8,
        delta: -2,
        label: "helped",
        attributed: true,
        direction: "lower-better",
      };
      store.add(outcome);

      const restored = new FileOutcomeStore(directory, files);
      assert.equal(restored.all()[0].id, "o-1");
      assert.equal(restored.forDecision("d-1")[0].label, "helped");
      assert.equal(restored.summary().helped, 1);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });
});
