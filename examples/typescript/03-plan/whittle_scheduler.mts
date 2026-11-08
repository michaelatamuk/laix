import {
  WhittleScheduler,
  whittleIndex,
} from "../../../packages/typescript/laix/src/index.ts";
import type { WhittleCandidate } from "../../../packages/typescript/laix/src/index.ts";

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

const high = candidate("high", 1);
const low = candidate("low", 0.1);
const schedule = new WhittleScheduler().schedule([low, high], { budget: 1 });

console.log(whittleIndex(high), whittleIndex(low));
console.log(schedule.selected[0]?.candidateId, schedule.deferred[0]?.candidateId);
