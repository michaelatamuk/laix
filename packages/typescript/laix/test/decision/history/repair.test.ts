import assert from "node:assert/strict";
import test from "node:test";

import { repairContinuity } from "../../../src/index.ts";

test("CDR supersedes the cheaper conflicting record", () => {
  const plan = repairContinuity([
    {
      id: "approval-1",
      kind: "approval",
      status: "rejected",
      refs: ["order-1"],
      cost: 1,
    },
    {
      id: "receipt-1",
      kind: "receipt",
      status: "executed",
      refs: ["order-1"],
      cost: 3,
    },
  ]);

  assert.deepEqual(plan.conflicts, [["approval-1", "receipt-1"]]);
  assert.equal(plan.actions[0]?.recordId, "approval-1");
  assert.equal(plan.actions[0]?.toStatus, "superseded");
  assert.equal(plan.totalCost, 1);
  assert.equal(plan.consistent, false);
});

test("CDR returns an empty plan for a consistent history", () => {
  const plan = repairContinuity([
    { id: "decision-1", kind: "decision", status: "final" },
  ]);

  assert.deepEqual(plan.conflicts, []);
  assert.equal(plan.actions.length, 0);
  assert.equal(plan.totalCost, 0);
  assert.equal(plan.consistent, true);
});

test("CDR exact repair beats greedy on a star", () => {
  const records = [
    { id: "a", kind: "decision", status: "final", conflicts: ["b"], cost: 1 },
    { id: "b", kind: "decision", status: "final", conflicts: ["c", "d"], cost: 2 },
    { id: "c", kind: "decision", status: "final", cost: 1 },
    { id: "d", kind: "decision", status: "final", cost: 1 },
  ];

  const greedy = repairContinuity(records);
  const exact = repairContinuity(records, undefined, { exact: true });

  assert.equal(greedy.totalCost, 3);
  assert.equal(exact.totalCost, 2);
  assert.deepEqual(exact.actions.map((action) => action.recordId), ["b"]);
  assert.equal(exact.method, "exact");
});

test("CDR honours explicit conflicts", () => {
  const plan = repairContinuity([
    {
      id: "a",
      kind: "decision",
      status: "final",
      conflicts: ["b"],
      cost: 0.1,
    },
    { id: "b", kind: "decision", status: "final", cost: 0.2 },
  ]);

  assert.equal(plan.actions[0]?.recordId, "a");
});
