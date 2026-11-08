import assert from "node:assert/strict";
import test from "node:test";

import {
  WhittleScheduler,
  whittleIndex,
} from "../../../src/index.ts";
import type { WhittleCandidate } from "../../../src/index.ts";

function candidate(id: string, reward: number): WhittleCandidate {
  return {
    id,
    states: ["bad", "good"],
    start: "bad",
    activeTransitions: [
      { state: "bad", nextState: "good" },
      { state: "good", nextState: "good" },
    ],
    passiveTransitions: [
      { state: "bad", nextState: "bad" },
      { state: "good", nextState: "good" },
    ],
    activeReward: { bad: reward, good: 0.2 },
    passiveReward: { bad: 0, good: 0 },
    activeCost: 0.1,
    reviewCost: 1,
    discount: 0.9,
  };
}

test("higher active reward has a higher Whittle index", () => {
  const high = whittleIndex(candidate("high", 1));
  const low = whittleIndex(candidate("low", 0.1));

  assert.ok(high > low);
  assert.ok(high > 0);
});

test("Whittle scheduler allocates by index", () => {
  const schedule = new WhittleScheduler().schedule(
    [candidate("low", 0.1), candidate("high", 1)],
    { budget: 1 },
  );

  assert.equal(schedule.selected[0]?.candidateId, "high");
  assert.equal(schedule.deferred[0]?.candidateId, "low");
  assert.equal(schedule.spent, 1);
});
