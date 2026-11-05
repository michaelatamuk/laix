import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ExecutionBridge, Saga } from "../src/index.ts";
import type { ActionOption, ExecutionStep } from "../src/index.ts";

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

describe("execution bridge saga", () => {
  it("compensates completed receipts", () => {
    const log: string[] = [];
    const bridge = new ExecutionBridge({
      handlers: {
        reserve: () => ({ reserved: true }),
        charge: () => {
          throw new Error("declined");
        },
      },
      undoHandlers: {
        reserve: () => {
          log.push("released");
          return { released: true };
        },
      },
    });
    const result = bridge.runSteps(
      [
        {
          action: { id: "a1", verb: "act", name: "reserve" } satisfies ActionOption,
        },
        {
          action: { id: "a2", verb: "act", name: "charge" } satisfies ActionOption,
        },
      ] satisfies ExecutionStep[],
      { actor: "checkout" },
    );

    assert.deepEqual(result.completed, ["reserve"]);
    assert.deepEqual(result.compensated, ["reserve"]);
    assert.equal(result.error, "Error: declined");
    assert.deepEqual(result.receipts.map((item) => item.status), ["executed", "failed"]);
    assert.deepEqual(log, ["released"]);
  });
});
