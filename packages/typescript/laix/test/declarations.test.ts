import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

const declarations = readFileSync(new URL("../types.d.ts", import.meta.url), "utf8");

const publicNames = [
  "AsyncHandler",
  "AttributeValue",
  "ExecutionTimeout",
  "FileOutcomeStore",
  "FileStateStore",
  "RetryOptions",
];

describe("public declarations", () => {
  it("covers the new public APIs", () => {
    for (const name of publicNames) {
      assert.match(
        declarations,
        new RegExp(`export (?:class|interface|type|function) ${name}\\b`),
        `${name} is missing from types.d.ts`,
      );
    }
  });
});
