import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CommitmentGraph,
  CommitmentLedger,
  CommitmentPlanner,
  type ActionOption,
  type Commitment,
  type CommitmentRef,
  type PlannerInput,
} from "../../../src/index.ts";

const supplierRef: CommitmentRef = {
  owner: "supplier",
  ledger: "supplier",
  id: "c2",
};

function localLedger(): CommitmentLedger {
  return new CommitmentLedger([
    {
      id: "c1",
      subject: "deliver to the customer",
      externalDependsOn: [supplierRef],
    },
  ]);
}

function reported(): Commitment {
  return {
    id: "c2",
    subject: "ship the part",
    owner: "supplier",
    ledger: "supplier",
    status: "done",
    source: "reported",
  };
}

describe("commitment graph", () => {
  it("distinguishes reported from verified external dependencies", () => {
    const graph = new CommitmentGraph(localLedger(), [reported()]);

    assert.equal(graph.blocked(localLedger().get("c1")), false);
    assert.equal(
      graph.blocked(localLedger().get("c1"), { requireVerified: true }),
      true,
    );
    assert.deepEqual(
      graph
        .blockers(localLedger().get("c1"), { requireVerified: true })
        .map((item) => [item.ref.id, item.reason]),
      [["c2", "unverified"]],
    );
    assert.deepEqual(
      graph.unverifiedRefs().map((ref) => ref.id),
      ["c2"],
    );
  });

  it("accepts an external dependency once it is verified", () => {
    const graph = new CommitmentGraph(localLedger(), [
      { ...reported(), source: "verified", verifiedAt: "2026-11-01T09:00:00Z" },
    ]);

    assert.equal(
      graph.blocked(localLedger().get("c1"), { requireVerified: true }),
      false,
    );
  });

  it("finds missing references and dependency cycles", () => {
    const missing: CommitmentRef = { owner: "other", ledger: "other", id: "x" };
    const ledger = new CommitmentLedger([
      { id: "a", subject: "a", externalDependsOn: [missing] },
      { id: "b", subject: "b", dependsOn: ["c"] },
      { id: "c", subject: "c", dependsOn: ["b"] },
    ]);
    const graph = new CommitmentGraph(ledger);

    assert.deepEqual(graph.missingRefs(), [missing]);
    assert.equal(graph.cycles().length > 0, true);
    assert.deepEqual(
      new Set(graph.cycles()[0]!.map((ref) => ref.id)),
      new Set(["b", "c"]),
    );
  });

  it("reports impact, chain and critical path", () => {
    const graph = new CommitmentGraph(
      new CommitmentLedger([
        { id: "a", subject: "a" },
        { id: "b", subject: "b", dependsOn: ["a"] },
        { id: "c", subject: "c", dependsOn: ["b"] },
      ]),
    );

    assert.deepEqual(
      graph.impact({ owner: "local", ledger: null, id: "a" }).map((item) => item.id),
      ["b", "c"],
    );
    assert.deepEqual(
      graph.chain({ owner: "local", ledger: null, id: "c" }).map((item) => item.id),
      ["c", "b", "a"],
    );
    assert.deepEqual(
      graph.criticalPath().map((item) => item.id),
      ["c", "b", "a"],
    );
  });

  it("picks the next actionable local commitment", () => {
    const graph = new CommitmentGraph(
      new CommitmentLedger([
        { id: "done", subject: "done", status: "done" },
        { id: "blocked", subject: "blocked", dependsOn: ["open"] },
        { id: "open", subject: "open" },
      ]),
    );

    assert.equal(graph.nextActionable()?.id, "open");
    assert.deepEqual(
      graph.blockedOpen().map((item) => item.id),
      ["blocked"],
    );
  });
});

function problem(
  options: ActionOption[],
  attributes: Record<string, unknown>,
): PlannerInput {
  return {
    subject: "deliver",
    at: "2026-11-01T10:00:00Z",
    options,
    attributes,
  };
}

describe("commitment graph planning", () => {
  it("rejects a hard commitment blocked by an unverified dependency", () => {
    const graph = new CommitmentGraph(localLedger(), [reported()]);
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          {
            id: "finish",
            verb: "act",
            name: "finish the delivery",
            expectedBenefit: 1,
            params: { commitments: { fulfills: ["c1"], hard: true } },
          },
          {
            id: "wait",
            verb: "wait",
            name: "wait for verification",
            expectedBenefit: 0.1,
          },
        ],
        { commitment_graph: graph },
      ),
    );

    assert.equal(plan.actionId, "wait");
    const alternatives = plan.alternatives as Array<Record<string, unknown>>;
    assert.match(
      String(alternatives.find((row) => row.action_id === "finish")?.rejected_because),
      /blocked hard commitment/,
    );
  });

  it("accepts a hard commitment once the dependency is verified", () => {
    const graph = new CommitmentGraph(localLedger(), [
      { ...reported(), source: "verified", verifiedAt: "2026-11-01T09:00:00Z" },
    ]);
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          {
            id: "finish",
            verb: "act",
            name: "finish the delivery",
            expectedBenefit: 1,
            params: { commitments: { fulfills: ["c1"], hard: true } },
          },
          {
            id: "wait",
            verb: "wait",
            name: "wait for verification",
            expectedBenefit: 0.1,
          },
        ],
        { commitment_graph: graph },
      ),
    );

    assert.equal(plan.actionId, "finish");
  });

  it("builds a graph from external commitments in the attributes", () => {
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          {
            id: "finish",
            verb: "act",
            name: "finish the delivery",
            expectedBenefit: 1,
            params: { commitments: { fulfills: ["c1"], hard: true } },
          },
          {
            id: "wait",
            verb: "wait",
            name: "wait for verification",
            expectedBenefit: 0.1,
          },
        ],
        {
          commitments: [
            {
              id: "c1",
              subject: "deliver to the customer",
              externalDependsOn: [supplierRef],
            },
          ],
          external_commitments: [reported()],
        },
      ),
    );

    assert.equal(plan.actionId, "wait");
  });
});
