import { repairContinuity } from "../../../../../packages/typescript/laix/src/index.ts";

const records = [
  { id: "a", kind: "decision", status: "final", conflicts: ["b"], cost: 1 },
  { id: "b", kind: "decision", status: "final", conflicts: ["c", "d"], cost: 2 },
  { id: "c", kind: "decision", status: "final", cost: 1 },
  { id: "d", kind: "decision", status: "final", cost: 1 },
];

const greedy = repairContinuity(records);
const exact = repairContinuity(records, undefined, { exact: true });

console.log(greedy.totalCost, exact.totalCost, exact.actions.map((action) => action.recordId));
