import assert from "node:assert/strict";
import test from "node:test";

import { AttentionScheduler } from "../../../../src/index.ts";

test("AADS prefers the urgent high-risk review", () => {
  const schedule = new AttentionScheduler().schedule(
    [
      {
        id: "urgent",
        risk: 0.9,
        commitment: true,
        reviewCost: 1,
        deadline: "2026-11-01T10:01:00Z",
      },
      {
        id: "routine",
        risk: 0.1,
        reviewCost: 1,
        deadline: "2026-11-01T11:00:00Z",
      },
    ],
    { now: "2026-11-01T10:00:00Z", budget: 1 },
  );

  assert.equal(schedule.selected[0]?.candidateId, "urgent");
  assert.equal(schedule.spent, 1);
  assert.equal(schedule.deferred[0]?.candidateId, "routine");
});

test("AADS respects the attention budget", () => {
  const schedule = new AttentionScheduler().schedule(
    [
      { id: "a", risk: 0.8, reviewCost: 0.75 },
      { id: "b", risk: 0.6, reviewCost: 0.75 },
    ],
    { now: "2026-11-01T10:00:00Z", budget: 1 },
  );

  assert.deepEqual(
    schedule.selected.map((row) => row.candidateId),
    ["a"],
  );
  assert.equal(schedule.deferred[0]?.candidateId, "b");
  assert.equal(schedule.deferred[0]?.reason, "attention budget exhausted");
});

test("AADS returns an empty schedule", () => {
  const schedule = new AttentionScheduler().schedule([], {
    now: "2026-11-01T10:00:00Z",
  });

  assert.equal(schedule.selected.length, 0);
  assert.equal(schedule.deferred.length, 0);
  assert.equal(schedule.spent, 0);
});
