import {
  CommitmentGraph,
  CommitmentLedger,
  CommitmentPlanner,
  type Commitment,
  type CommitmentRef,
  type PlannerInput,
} from "../../../../packages/typescript/laix/src/index.ts";

const NOW = "2026-11-01T10:00:00Z";
const SUPPLIER: CommitmentRef = {
  owner: "supplier",
  ledger: "supplier",
  id: "ship",
};

function localLedger(): CommitmentLedger {
  return new CommitmentLedger([
    {
      id: "deliver",
      subject: "deliver to the customer",
      externalDependsOn: [SUPPLIER],
    },
  ]);
}

function shipment(source: "reported" | "verified", verifiedAt?: string): Commitment {
  return {
    id: "ship",
    subject: "ship the part",
    owner: "supplier",
    ledger: "supplier",
    status: "done",
    source,
    verifiedAt: verifiedAt ?? null,
  };
}

function problem(graph: CommitmentGraph): PlannerInput {
  return {
    subject: "deliver",
    at: NOW,
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
  };
}

function decide(
  external: Commitment | null,
  options: { requireVerified?: boolean; maxVerificationAgeMs?: number } = {},
): string {
  const graph = new CommitmentGraph(
    localLedger(),
    external ? [external] : [],
  );
  return new CommitmentPlanner(undefined, {}, options)
    .solve(problem(graph))
    .actionId!;
}

const cases: Array<[string, Commitment | null, number | undefined, string]> = [
  ["fresh", shipment("verified", "2026-11-01T09:30:00Z"), 24, "finish"],
  ["stale", shipment("verified", "2026-10-30T09:00:00Z"), 24, "wait"],
  ["reported", shipment("reported"), 24, "wait"],
  ["missing", null, 24, "wait"],
];

let passed = 0;
let total = 0;
for (const [name, external, maxAgeHours, expected] of cases) {
  total += 1;
  const actual = decide(external, {
    maxVerificationAgeMs:
      maxAgeHours === undefined ? undefined : maxAgeHours * 60 * 60 * 1000,
  });
  passed += actual === expected ? 1 : 0;
  console.log(name, actual);
}

const reportedAllowed = decide(shipment("reported"), {
  requireVerified: false,
});
total += 1;
passed += reportedAllowed === "finish" ? 1 : 0;
console.log("reported-allowed", reportedAllowed);

console.log(`${passed}/${total}`);
