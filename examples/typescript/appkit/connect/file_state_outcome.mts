import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  ExperienceState,
  FileOutcomeStore,
  FileStateStore,
} from "../../../../packages/typescript/laix/src/index.ts";
import type {
  Outcome,
  StateFiles,
} from "../../../../packages/typescript/laix/src/index.ts";

const files: StateFiles = {
  join: (directory, name) => join(directory, name),
  read: (path) => (existsSync(path) ? readFileSync(path, "utf8") : null),
  write: (path, text) => writeFileSync(path, text, "utf8"),
  remove: (path) => {
    if (existsSync(path)) unlinkSync(path);
  },
};

const directory = mkdtempSync(join(tmpdir(), "laix-file-state-"));
try {
  const stateStore = new FileStateStore(directory, files);
  const state = new ExperienceState("weekly review", "decide");
  stateStore.save("review-1", state);
  const loaded = stateStore.load("review-1");

  const outcomeStore = new FileOutcomeStore(directory, files);
  const outcome: Outcome = {
    id: "o-1",
    decisionId: "DEC-1",
    metric: "time_to_review",
    before: 10,
    after: 8,
    delta: -2,
    label: "helped",
    attributed: true,
    direction: "lower-better",
  };
  outcomeStore.add(outcome);
  const restored = new FileOutcomeStore(directory, files);

  console.log(loaded?.phase ?? "missing", restored.summary().helped);
} finally {
  rmSync(directory, { recursive: true, force: true });
}
