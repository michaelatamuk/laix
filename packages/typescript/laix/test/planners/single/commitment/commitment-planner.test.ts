import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CommitmentPlanner,
  UtilityPlanner,
  UtilityModel,
} from "../../../../src/index.ts";
import type { ActionOption, Commitment, PlannerInput } from "../../../../src/index.ts";

function problem(
  options: ActionOption[],
  commitments: Commitment[] = [],
): PlannerInput {
  return {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options,
    attributes: { commitments },
  };
}

function option(
  id: string,
  benefit: number,
  commitments?: Record<string, unknown>,
): ActionOption {
  return {
    id,
    verb: "act",
    name: id,
    expectedBenefit: benefit,
    params: commitments ? { commitments } : {},
  };
}

describe("commitment-aware planning", () => {
  it("changes the choice when an option breaks a promise", () => {
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          option("send-now", 1.0, { violates: ["c1"] }),
          option("send-later", 0.6, { fulfills: ["c1"] }),
        ],
        [{ id: "c1", subject: "send the report", priority: 1 }],
      ),
    );

    assert.equal(plan.verb, "act");
    assert.equal(plan.actionId, "send-later");
    assert.equal(plan.reasonCode, "commitment_aware");
    assert.deepEqual(plan.attributes?.commitments_fulfilled, ["c1"]);
  });

  it("weights a due commitment more", () => {
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          option("do-later", 0.6, { fulfills: ["later"] }),
          option("do-now", 0.6, { fulfills: ["now"] }),
        ],
        [
          { id: "later", subject: "not due", due: "2026-11-02T09:00:00Z" },
          { id: "now", subject: "due now", due: "2026-11-01T09:00:00Z" },
        ],
      ),
    );

    assert.equal(plan.actionId, "do-now");
    assert.deepEqual(plan.attributes?.commitments_due_fulfilled, ["now"]);
  });

  it("blocks a hard violation", () => {
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          option("break", 1.0, { violates: ["c1"], hard: true }),
          option("keep", 0.4, { fulfills: ["c1"] }),
        ],
        [{ id: "c1", subject: "do not break this" }],
      ),
    );

    assert.equal(plan.actionId, "keep");
    const alternatives = plan.alternatives as Array<Record<string, unknown>>;
    assert.match(
      String(alternatives.find((row) => row.action_id === "break")?.rejected_because),
      /hard commitment/,
    );
  });

  it("blocks fulfillment until a dependency is done", () => {
    const blocked = new CommitmentPlanner().solve(
      problem(
        [
          option("do-c0", 0.5, { fulfills: ["c0"] }),
          option("do-c1", 0.5, { fulfills: ["c1"] }),
        ],
        [
          { id: "c0", subject: "prerequisite" },
          { id: "c1", subject: "dependent", dependsOn: ["c0"] },
        ],
      ),
    );
    assert.equal(blocked.actionId, "do-c0");

    const unblocked = new CommitmentPlanner().solve(
      problem(
        [
          option("do-c0", 0.5),
          option("do-c1", 0.5, { fulfills: ["c1"] }),
        ],
        [
          { id: "c0", subject: "prerequisite", status: "done" },
          { id: "c1", subject: "dependent", dependsOn: ["c0"] },
        ],
      ),
    );
    assert.equal(unblocked.actionId, "do-c1");
  });

  it("scales the reward by priority", () => {
    const plan = new CommitmentPlanner().solve(
      problem(
        [
          option("do-low", 0.5, { fulfills: ["low"] }),
          option("do-high", 0.5, { fulfills: ["high"] }),
        ],
        [
          { id: "low", subject: "low", priority: 0.1 },
          { id: "high", subject: "high", priority: 1 },
        ],
      ),
    );

    assert.equal(plan.actionId, "do-high");
  });

  it("matches the utility planner when there are no commitments", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
    ];
    assert.equal(
      new CommitmentPlanner().solve(problem(options)).actionId,
      new UtilityPlanner().solve(problem(options)).actionId,
    );
  });

  it("rejects a negative weight", () => {
    assert.throws(
      () => new CommitmentPlanner(new UtilityModel(), { violate: -1 }),
    );
  });
});
