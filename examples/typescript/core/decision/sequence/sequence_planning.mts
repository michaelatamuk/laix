import {
  CABBPlanner,
  HumanAttentionBudget,
  ReplanPlanner,
  RolloutPlanner,
} from "../../../../../packages/typescript/laix/src/index.ts";
import type { DecisionScenario } from "../../../../../packages/typescript/laix/src/index.ts";

function scenario(): DecisionScenario {
  return {
    steps: [
      {
        at: "2026-11-01T10:00:00Z",
        options: [
          {
            id: "pay",
            verb: "act",
            name: "pay the invoice",
            expectedBenefit: 0.95,
            risk: 0.05,
            requiresApproval: true,
            reversible: false,
            interruptCost: 0.6,
            params: { commitments: { violates: ["c1"] } },
          },
          {
            id: "ask",
            verb: "ask",
            name: "ask the owner",
            expectedBenefit: 0.6,
            interruptCost: 0.2,
            params: { commitments: { fulfills: ["c1"] } },
          },
        ],
      },
      {
        at: "2026-11-01T11:00:00Z",
        options: [
          { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.2 },
          { id: "verify", verb: "verify", name: "verify", expectedBenefit: 0.4 },
        ],
      },
    ],
    commitments: [
      {
        id: "c1",
        subject: "ask the owner before paying",
        due: "2026-11-01T09:00:00Z",
      },
    ],
    humanAttentionBudget: new HumanAttentionBudget({ total: 2, spent: 0.5 }),
  };
}

const exact = new CABBPlanner().plan(scenario());
const rollout = new RolloutPlanner().plan(scenario());
const repair = new ReplanPlanner().replan(scenario(), ["ask"]);

console.log(
  exact.actions.join(","),
  exact.score,
  exact.optimal,
  rollout.actions.join(","),
  repair.actions.join(","),
);
