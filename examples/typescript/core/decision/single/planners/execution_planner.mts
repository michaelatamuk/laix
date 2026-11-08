import {
  ExecutionRiskPlanner,
} from "../../../../../../packages/typescript/laix/src/index.ts";
import type {
  ActionOption,
  PlannerInput,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const options: ActionOption[] = [
  {
    id: "delete-now",
    verb: "act",
    name: "delete now",
    expectedBenefit: 0.8,
    reversible: false,
  },
  {
    id: "archive",
    verb: "act",
    name: "archive",
    expectedBenefit: 0.7,
  },
];

const problem: PlannerInput = {
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options,
  attributes: {},
};

const plan = new ExecutionRiskPlanner().solve(problem);
console.log(plan.actionId, plan.reasonCode, plan.reversible);
