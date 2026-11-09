import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const dist = fileURLToPath(new URL("../dist/", import.meta.url));

function declarationFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return declarationFiles(path);
    return entry.name.endsWith(".d.ts") ? [path] : [];
  });
}

const declarations = declarationFiles(dist)
  .map((path) => readFileSync(path, "utf8"))
  .join("\n");

const publicNames = [
  "AsyncHandler",
  "AttributeValue",
  "Breakdown",
  "DecisionTimeline",
  "ExecutionRiskPlanner",
  "ExecutionTimeout",
  "FileOutcomeStore",
  "FileStateStore",
  "HumanAttentionBudget",
  "LiveCompositePlanner",
  "Phase",
  "RetryOptions",
  "RuntimeDecision",
  "Situation",
];

describe("public declarations", () => {
  it("covers the public APIs", () => {
    for (const name of publicNames) {
      assert.match(
        declarations,
        new RegExp(`export (?:declare )?(?:class|interface|type|function|const) ${name}\\b`),
        `${name} is missing from the generated declarations`,
      );
    }
  });

  it("uses .js import specifiers", () => {
    assert.doesNotMatch(
      declarations,
      /from\s+["'][^"']+\.ts["']/,
      "generated declarations still contain .ts import specifiers",
    );
  });
});
