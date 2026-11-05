import {
  LiveDecisionEngine,
} from "../../../packages/typescript/laix/src/index.ts";
import type {
  ActionOption,
  Commitment,
  DecisionProblem,
} from "../../../packages/typescript/laix/src/index.ts";

const commitments: Commitment[] = [
  {
    id: "c1",
    subject: "send the report",
    due: "2026-11-01T09:00:00Z",
  },
];

const options: ActionOption[] = [
  {
    id: "fast",
    verb: "act",
    name: "fast",
    expectedBenefit: 1,
    reversible: false,
    interruptCost: 0.6,
    params: { commitments: { violates: ["c1"] } },
  },
  {
    id: "safe",
    verb: "act",
    name: "safe",
    expectedBenefit: 0.6,
    params: { commitments: { fulfills: ["c1"] } },
  },
];

const problem: DecisionProblem = {
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options,
  attributes: { commitments },
};

const plan = new LiveDecisionEngine().solve(problem);
const fulfilled = (plan.attributes?.commitments_fulfilled as string[]).join(",");
console.log(plan.actionId, plan.reasonCode, fulfilled);
