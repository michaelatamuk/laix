import { CAVODPlanner } from "../../../packages/typescript/laix/src/index.ts";
import type { PlannerInput } from "../../../packages/typescript/laix/src/index.ts";

const problem: PlannerInput = {
  subject: "invoice 4832",
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
    {
      id: "wait",
      verb: "wait",
      name: "wait for the next review",
      expectedBenefit: 0.2,
    },
  ],
  attributes: {
    commitments: [
      {
        id: "c1",
        subject: "ask the owner before paying",
        due: "2026-11-01T09:00:00Z",
      },
    ],
    human_attention_budget: { total: 2, spent: 0.5 },
    uncertainty: 0.8,
  },
};

const plan = new CAVODPlanner().solve(problem);
console.log(
  plan.actionId,
  plan.reasonCode,
  plan.attributes?.information_value,
  plan.attributes?.option_value,
);
