import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { Saga } from "../src/index.ts";

describe("execution saga", () => {
  it("compensates completed steps in reverse", () => {
    const log: string[] = [];
    const result = new Saga().run([
      {
        name: "first",
        forward: () => {
          log.push("first");
          return {};
        },
        compensate: () => {
          log.push("undo first");
          return {};
        },
      },
      {
        name: "second",
        forward: () => {
          log.push("second");
          throw new Error("boom");
        },
      },
    ]);

    assert.deepEqual(result.completed, ["first"]);
    assert.deepEqual(result.compensated, ["first"]);
    assert.match(result.error ?? "", /Error: boom/);
    assert.deepEqual(log, ["first", "second", "undo first"]);
  });

  it("succeeds without compensation", () => {
    const result = new Saga().run([{ name: "first", forward: () => ({}) }]);

    assert.deepEqual(result.completed, ["first"]);
    assert.deepEqual(result.compensated, []);
    assert.equal(result.error, undefined);
  });
});
