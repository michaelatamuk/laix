import {
  CommitmentLedger,
  CommitmentPlanner,
  InMemoryCommitmentResolver,
  resolveCommitmentGraph,
  type Commitment,
} from "../../../../packages/typescript/laix/src/index.ts";

const local = new CommitmentLedger([
  {
    id: "deliver",
    subject: "deliver to the customer",
    externalDependsOn: [{ owner: "supplier", ledger: "supplier", id: "ship" }],
  },
]);

function plan(source: "reported" | "verified"): string {
  const shipment: Commitment = {
    id: "ship",
    subject: "ship the part",
    owner: "supplier",
    ledger: "supplier",
    status: "done",
    source,
  };
  const graph = resolveCommitmentGraph(
    local,
    new InMemoryCommitmentResolver([shipment]),
  );
  return new CommitmentPlanner().solve({
    subject: "deliver",
    at: "2026-11-01T10:00:00Z",
    options: [
      {
        id: "finish",
        verb: "act",
        name: "finish the delivery",
        expectedBenefit: 1,
        params: { commitments: { fulfills: ["deliver"], hard: true } },
      },
      {
        id: "wait",
        verb: "wait",
        name: "wait for verification",
        expectedBenefit: 0.1,
      },
    ],
    attributes: { commitment_graph: graph },
  }).actionId;
}

console.log(plan("reported"), plan("verified"));
