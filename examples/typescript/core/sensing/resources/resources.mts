/** Cheap detectors always run. Admit a deep call only when it pays off. */
import { ResourceScheduler } from "../../../../../packages/typescript/laix/src/index.ts";

const plan = new ResourceScheduler().schedule(
  [
    { name: "camera", tier: "cheap", cost: 0 },
    { name: "read-page", tier: "deep", cost: 0.1, latencyMs: 800, informationGain: 0.9 },
    { name: "full-audio", tier: "deep", cost: 2, latencyMs: 800, informationGain: 0.9 },
  ],
  { budget: { maxDeepCalls: 2, maxCost: 1, maxLatencyMs: 2000 }, uncertainty: 0.8 },
);
console.log(plan.allowed, plan.skipped.map((item) => item.name));
