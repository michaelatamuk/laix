import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import {
  CommitmentGraph,
  CommitmentLedger,
  CommitmentPlanner,
  UtilityModel,
  type ActionOption,
  type Commitment,
  type CommitmentRef,
  type PlannerInput,
} from "../../../src/index.ts";

interface RawCase {
  id: string;
  target: string;
  chain_from?: string;
  impact_from?: string;
  local: Array<Record<string, unknown>>;
  external: Array<Record<string, unknown>>;
  expected: Record<string, unknown>;
}

interface RawPlannerCase {
  id: string;
  require_verified: boolean;
  local: Array<Record<string, unknown>>;
  external: Array<Record<string, unknown>>;
  options: Array<Record<string, unknown>>;
  expected_action_id: string;
  expected_blocked_by: Array<Record<string, unknown>>;
}

const fixture = JSON.parse(
  readFileSync(
    new URL("../../../../../contracts/commitment-graph.v1.json", import.meta.url),
    "utf8",
  ),
) as { cases: RawCase[]; planner_cases: RawPlannerCase[] };

function asRef(raw: Record<string, unknown>): CommitmentRef {
  return {
    owner: String(raw.owner),
    ledger: (raw.ledger as string | null | undefined) ?? null,
    id: String(raw.id),
  };
}

function asCommitment(raw: Record<string, unknown>): Commitment {
  return {
    id: String(raw.id),
    subject: String(raw.subject ?? ""),
    due: (raw.due as string | null | undefined) ?? null,
    status: (raw.status as Commitment["status"]) ?? "open",
    dependsOn: ((raw.depends_on as string[] | undefined) ?? []).slice(),
    priority: (raw.priority as number | undefined) ?? 0.5,
    payload: { ...((raw.payload as Record<string, unknown> | undefined) ?? {}) },
    owner: String(raw.owner ?? "local"),
    ledger: (raw.ledger as string | null | undefined) ?? null,
    source: (raw.source as Commitment["source"]) ?? "local",
    verifiedAt: (raw.verified_at as string | null | undefined) ?? null,
    externalDependsOn: (
      (raw.external_depends_on as Record<string, unknown>[] | undefined) ?? []
    ).map(asRef),
  };
}

function asRefs(items: CommitmentRef[]): Array<Record<string, unknown>> {
  return items.map((item) => ({
    owner: item.owner,
    ledger: item.ledger ?? null,
    id: item.id,
  }));
}

function asActionOption(raw: Record<string, unknown>): ActionOption {
  return {
    id: String(raw.id),
    verb: raw.verb as ActionOption["verb"],
    name: String(raw.name),
    expectedBenefit: (raw.expected_benefit as number | undefined) ?? 0.5,
    params: { ...((raw.params as Record<string, unknown> | undefined) ?? {}) },
  };
}

describe("commitment graph parity fixture", () => {
  for (const testCase of fixture.cases) {
    it(testCase.id, () => {
      const local = new CommitmentLedger(testCase.local.map(asCommitment));
      const graph = new CommitmentGraph(
        local,
        testCase.external.map(asCommitment),
      );
      const target = local.get(testCase.target);
      const expected = testCase.expected;

      assert.equal(graph.blocked(target), expected.blocked);
      assert.equal(
        graph.blocked(target, { requireVerified: true }),
        expected.blocked_verified,
      );
      assert.deepEqual(
        graph.blockers(target, { requireVerified: true }).map((blocker) => ({
          owner: blocker.ref.owner,
          ledger: blocker.ref.ledger ?? null,
          id: blocker.ref.id,
          reason: blocker.reason,
        })),
        expected.blockers,
      );
      assert.deepEqual(asRefs(graph.missingRefs()), expected.missing_refs);
      assert.deepEqual(asRefs(graph.unverifiedRefs()), expected.unverified_refs);

      if (expected.chain !== undefined) {
        assert.deepEqual(
          graph
            .chain({
              owner: "local",
              ledger: null,
              id: testCase.chain_from!,
            })
            .map((item) => item.id),
          expected.chain,
        );
      }
      if (expected.impact !== undefined) {
        assert.deepEqual(
          graph
            .impact({
              owner: "local",
              ledger: null,
              id: testCase.impact_from!,
            })
            .map((item) => item.id),
          expected.impact,
        );
      }
      if (expected.critical_path !== undefined) {
        assert.deepEqual(
          graph.criticalPath().map((item) => item.id),
          expected.critical_path,
        );
      }
      if (expected.cycles !== undefined) {
        const actual = graph
          .cycles()
          .map((cycle) => [...new Set(cycle.map((item) => item.id))].sort())
          .map((cycle) => JSON.stringify(cycle))
          .sort();
        const wanted = (expected.cycles as string[][])
          .map((cycle) => JSON.stringify([...new Set(cycle)].sort()))
          .sort();
        assert.deepEqual(actual, wanted);
      }
    });
  }
});

describe("commitment planner parity fixture", () => {
  for (const testCase of fixture.planner_cases) {
    it(testCase.id, () => {
      const graph = new CommitmentGraph(
        new CommitmentLedger(testCase.local.map(asCommitment)),
        testCase.external.map(asCommitment),
      );
      const problem: PlannerInput = {
        subject: "deliver",
        at: "2026-11-01T10:00:00Z",
        options: testCase.options.map(asActionOption),
        attributes: { commitment_graph: graph },
      };
      const result = new CommitmentPlanner(
        new UtilityModel(),
        {},
        { requireVerified: testCase.require_verified },
      ).solve(problem);

      assert.equal(result.actionId, testCase.expected_action_id);
      if (result.actionId === "finish") {
        assert.deepEqual(
          result.attributes?.commitments_blocked_by,
          testCase.expected_blocked_by,
        );
      } else {
        const alternatives = result.alternatives as Array<
          Record<string, unknown>
        >;
        const finish = alternatives.find((row) => row.action_id === "finish");
        assert.deepEqual(finish?.blocked_by, testCase.expected_blocked_by);
      }
    });
  }

  it("round-trips a graph through toDict and fromDict", () => {
    const graph = new CommitmentGraph(
      new CommitmentLedger([{ id: "a", subject: "a" }]),
      [
        {
          id: "b",
          subject: "b",
          owner: "other",
          ledger: "other",
          source: "reported",
        },
      ],
    );
    const payload = graph.toDict() as {
      local: { commitments?: Commitment[] };
      external: Commitment[];
    };
    const restored = CommitmentGraph.fromDict(payload);

    assert.deepEqual(restored.toDict(), graph.toDict());
    assert.deepEqual(
      restored.commitments.map((item) => item.id),
      ["a", "b"],
    );
  });
});
