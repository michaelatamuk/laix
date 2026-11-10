import {
  CommitmentGraph,
  CommitmentLedger,
  CommitmentPlanner,
  commitmentVerificationCounterfactual,
  type CommitmentRef,
  type PlannerInput,
} from "../../../../../packages/typescript/laix/src/index.ts";

const supplier: CommitmentRef = {
  owner: "supplier",
  ledger: "supplier",
  id: "ship",
};
const local = new CommitmentLedger([
  {
    id: "deliver",
    subject: "deliver the order",
    externalDependsOn: [supplier],
  },
]);
const problem: PlannerInput = {
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
  attributes: {
    commitment_graph: new CommitmentGraph(local, [
      {
        id: "ship",
        subject: "ship the part",
        owner: "supplier",
        ledger: "supplier",
        status: "done",
        source: "reported",
      },
    ]),
  },
};
const result = commitmentVerificationCounterfactual(
  problem,
  new CommitmentPlanner(),
);
const flip = result.flips[0]!;

console.log(result.base_action_id, flip.name, flip.counterfactual_action_id);
