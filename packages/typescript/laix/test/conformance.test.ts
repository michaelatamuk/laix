import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { decideSignalAttention } from "../src/index.ts";

const fixture = JSON.parse(
  readFileSync(new URL("../../../contracts/signal-attention.v1.json", import.meta.url), "utf8"),
);

describe("canonical attention contract", () => {
  for (const testCase of fixture.cases) {
    it(testCase.id, () => {
      const decisions = decideSignalAttention(testCase.context, testCase.signals);
      const byId = new Map(decisions.map((decision) => [decision.signalId, decision]));
      for (const expected of testCase.expected) {
        const actual = byId.get(expected.signalId);
        assert.ok(actual, `${testCase.id}: no decision for ${expected.signalId}`);
        assert.equal(actual.verb, expected.verb, `${testCase.id}/${expected.signalId}: action`);
        if (expected.reason_code !== undefined) {
          assert.equal(actual.reasonCode, expected.reason_code, `${testCase.id}/${expected.signalId}: reason`);
        }
        if (expected.deliver !== undefined) {
          assert.equal(actual.deliver, expected.deliver, `${testCase.id}/${expected.signalId}: deliver`);
        }
        if (expected.record !== undefined) {
          assert.equal(actual.record, expected.record, `${testCase.id}/${expected.signalId}: record`);
        }
        if (expected.requires_approval !== undefined) {
          assert.equal(actual.requiresApproval, expected.requires_approval, `${testCase.id}/${expected.signalId}: approval`);
        }
        if (typeof expected.score === "number") {
          assert.ok(Math.abs(actual.score - expected.score) <= 0.01, `${testCase.id}/${expected.signalId}: score`);
        }
        if (typeof expected.cost_of_waiting === "number") {
          assert.ok(
            Math.abs(actual.costOfWaiting - expected.cost_of_waiting) <= 0.01,
            `${testCase.id}/${expected.signalId}: cost`,
          );
        }
        if ("undo_hint" in expected) {
          assert.equal(actual.undoHint, expected.undo_hint ?? null, `${testCase.id}/${expected.signalId}: undo`);
        }
      }
    });
  }
});
