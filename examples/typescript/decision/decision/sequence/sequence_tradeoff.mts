import {
  CABBPlanner,
  HumanAttentionBudget,
  RolloutPlanner,
} from "../../../../../packages/typescript/laix/src/index.ts";
import type { DecisionScenario } from "../../../../../packages/typescript/laix/src/index.ts";

const scenario: DecisionScenario = {
  steps: [
    {
      at: "2026-11-01T10:00:00Z",
      options: [{ id: "start", verb: "wait", name: "start", expectedBenefit: 0.0 }],
    },
    {
      at: "2026-11-01T10:10:00Z",
      options: [
        { id: "big", verb: "act", name: "big", expectedBenefit: 1.0, interruptCost: 0.9 },
        { id: "small", verb: "act", name: "small", expectedBenefit: 0.6, interruptCost: 0.3 },
      ],
    },
    {
      at: "2026-11-01T10:20:00Z",
      options: [
        { id: "bonus", verb: "act", name: "bonus", expectedBenefit: 1.0, interruptCost: 0.6 },
        { id: "nothing", verb: "wait", name: "nothing", expectedBenefit: 0.1 },
      ],
    },
  ],
  humanAttentionBudget: new HumanAttentionBudget({ total: 1, spent: 0 }),
};

const exact = new CABBPlanner().plan(scenario);
const greedy = new RolloutPlanner().plan(scenario);

console.log("cabb", exact.actions.join(","), exact.score);
console.log("rollout", greedy.actions.join(","), greedy.score);
