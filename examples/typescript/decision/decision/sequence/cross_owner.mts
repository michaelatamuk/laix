import {
  CABBPlanner,
  type CommitmentRef,
  type DecisionScenario,
} from "../../../../../packages/typescript/laix/src/index.ts";

const supplier: CommitmentRef = {
  owner: "supplier",
  ledger: "supplier",
  id: "ship",
};

function scenario(
  source: "reported" | "verified",
  verifiedAt: string | null = null,
): DecisionScenario {
  return {
    steps: [
      {
        at: "2026-11-01T10:00:00Z",
        options: [
          {
            id: "deliver",
            verb: "act",
            name: "deliver",
            expectedBenefit: 1,
            params: { commitments: { fulfills: ["c1"], hard: true } },
          },
          { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.1 },
        ],
      },
    ],
    commitments: [
      { id: "c1", subject: "deliver", externalDependsOn: [supplier] },
      {
        id: "ship",
        subject: "ship",
        owner: "supplier",
        ledger: "supplier",
        status: "done",
        source,
        verifiedAt,
      },
    ],
  };
}

const reported = new CABBPlanner().plan(scenario("reported")).actions;
const verified = new CABBPlanner().plan(
  scenario("verified", "2026-11-01T09:30:00Z"),
).actions;

console.log(reported.join(","), verified.join(","));
