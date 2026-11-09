import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CommitmentLedger,
  InMemoryCommitmentResolver,
  resolveCommitmentGraph,
  resolveCommitmentGraphAsync,
  type AsyncCommitmentResolver,
  type Commitment,
  type CommitmentResolver,
} from "../src/index.ts";

function ship(source: "reported" | "verified" = "verified"): Commitment {
  return {
    id: "ship",
    subject: "ship the part",
    owner: "supplier",
    ledger: "supplier",
    status: "done",
    source,
    verifiedAt: source === "verified" ? "2026-11-01T09:30:00Z" : null,
  };
}

function local(): CommitmentLedger {
  return new CommitmentLedger([
    {
      id: "deliver",
      subject: "deliver to the customer",
      externalDependsOn: [
        { owner: "supplier", ledger: "supplier", id: "ship" },
      ],
    },
  ]);
}

describe("commitment resolver port", () => {
  it("builds a verified graph", () => {
    const resolver: CommitmentResolver = new InMemoryCommitmentResolver([
      ship(),
    ]);
    const ledger = local();
    const graph = resolveCommitmentGraph(ledger, resolver);

    assert.ok(
      graph.get({ owner: "supplier", ledger: "supplier", id: "ship" }),
    );
    assert.equal(
      graph.blocked(ledger.get("deliver"), { requireVerified: true }),
      false,
    );
    assert.deepEqual(graph.missingRefs(), []);
  });

  it("reports a missing commitment", () => {
    const ledger = local();
    const graph = resolveCommitmentGraph(
      ledger,
      new InMemoryCommitmentResolver(),
    );

    assert.equal(
      graph.blocked(ledger.get("deliver"), { requireVerified: true }),
      true,
    );
    assert.deepEqual(graph.missingRefs(), [
      { owner: "supplier", ledger: "supplier", id: "ship" },
    ]);
  });

  it("keeps a reported commitment unverified", () => {
    const ledger = local();
    const graph = resolveCommitmentGraph(
      ledger,
      new InMemoryCommitmentResolver([ship("reported")]),
    );

    assert.equal(
      graph.blocked(ledger.get("deliver"), { requireVerified: true }),
      true,
    );
    assert.deepEqual(
      graph.unverifiedRefs().map((ref) => ref.id),
      ["ship"],
    );
  });

  it("builds a graph from an async resolver", async () => {
    const resolver: AsyncCommitmentResolver = {
      resolve: async () => [ship()],
    };
    const ledger = local();
    const graph = await resolveCommitmentGraphAsync(ledger, resolver);

    assert.equal(
      graph.blocked(ledger.get("deliver"), { requireVerified: true }),
      false,
    );
  });
});
