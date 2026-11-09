import {
  CommitmentGraph,
  CommitmentLedger,
} from "../../../../packages/typescript/laix/src/index.ts";

const local = new CommitmentLedger([
  {
    id: "deliver",
    subject: "deliver to the customer",
    externalDependsOn: [{ owner: "supplier", ledger: "supplier", id: "ship" }],
  },
]);
const reported = {
  id: "ship",
  subject: "ship the part",
  owner: "supplier",
  ledger: "supplier",
  status: "done" as const,
  source: "reported" as const,
};
const graph = new CommitmentGraph(local, [reported]);

const blocker = graph
  .blockers(local.get("deliver"), { requireVerified: true })[0]!;
console.log(blocker.reason, blocker.ref.owner, blocker.ref.id);
