import {
  HumanAttentionPlanner,
} from "../../../packages/typescript/laix/src/index.ts";
import type {
  ActionOption,
  DecisionProblem,
} from "../../../packages/typescript/laix/src/index.ts";

const options: ActionOption[] = [
  { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
  { id: "act", verb: "act", name: "act", expectedBenefit: 0.6 },
];

const problem: DecisionProblem = {
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options,
  attributes: { attention_budget: 0.2, attention_spent: 0.2 },
};

const plan = new HumanAttentionPlanner().solve(problem);
console.log(plan.actionId, plan.reasonCode, plan.attributes?.attention_remaining);
