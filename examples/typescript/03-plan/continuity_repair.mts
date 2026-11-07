import { repairContinuity } from "../../../packages/typescript/laix/src/index.ts";

const plan = repairContinuity([
  {
    id: "approval-1",
    kind: "approval",
    status: "rejected",
    refs: ["order-1"],
    cost: 1,
  },
  {
    id: "receipt-1",
    kind: "receipt",
    status: "executed",
    refs: ["order-1"],
    cost: 3,
  },
]);

console.log(JSON.stringify(plan.conflicts));
console.log(
  JSON.stringify(
    plan.actions.map((action) => [
      action.recordId,
      action.action,
      action.toStatus,
    ]),
  ),
);
console.log(plan.totalCost);
