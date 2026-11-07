import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ExecutionRiskPlanner,
  UtilityPlanner,
  UtilityModel,
} from "../../../src/index.ts";
import type { ActionOption, PlannerInput, Receipt } from "../../../src/index.ts";

function problem(
  options: ActionOption[],
  attributes: Record<string, unknown> = {},
): PlannerInput {
  return {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options,
    attributes,
  };
}

function option(
  id: string,
  benefit: number,
  extra: Record<string, unknown> = {},
): ActionOption {
  return { id, verb: "act", name: id, expectedBenefit: benefit, ...extra };
}

describe("execution-aware planning", () => {
  it("prefers a reversible option when utility is equal", () => {
    const plan = new ExecutionRiskPlanner().solve(
      problem([
        option("reversible", 0.7, { reversible: true }),
        option("irreversible", 0.7, { reversible: false }),
      ]),
    );

    assert.equal(plan.actionId, "reversible");
    assert.equal(plan.reasonCode, "execution_aware");
  });

  it("penalizes an unknown outcome", () => {
    const plan = new ExecutionRiskPlanner().solve(
      problem([
        option("known", 0.7),
        option("unknown", 0.8, { params: { unknown_risk: 0.8 } }),
      ]),
    );

    assert.equal(plan.actionId, "known");
  });

  it("penalizes recovery cost", () => {
    const plan = new ExecutionRiskPlanner().solve(
      problem([
        option("cheap", 0.7),
        option("expensive", 0.8, { params: { recovery_cost: 1.0 } }),
      ]),
    );

    assert.equal(plan.actionId, "cheap");
  });

  it("penalizes an approval step", () => {
    const plan = new ExecutionRiskPlanner().solve(
      problem([
        option("direct", 0.7),
        option("approval", 0.75, { requiresApproval: true }),
      ]),
    );

    assert.equal(plan.actionId, "direct");
  });

  it("penalizes an unknown receipt", () => {
    const receipt: Receipt = {
      id: "r1",
      decisionId: "d1",
      actionName: "unknown",
      status: "unknown",
      actor: "operator",
    };
    const plan = new ExecutionRiskPlanner().solve(
      problem(
        [option("known", 0.7), option("unknown", 0.8)],
        { execution_receipts: [receipt] },
      ),
    );

    assert.equal(plan.actionId, "known");
  });

  it("penalizes a failed receipt and a pending approval", () => {
    const failed = new ExecutionRiskPlanner().solve(
      problem(
        [option("known", 0.7), option("failed", 0.8)],
        { execution_state: { failed: "failed" } },
      ),
    );
    assert.equal(failed.actionId, "known");

    const pending = new ExecutionRiskPlanner().solve(
      problem(
        [option("direct", 0.7), option("pending", 0.75)],
        { execution_state: { pending: "pending" } },
      ),
    );
    assert.equal(pending.actionId, "direct");
  });

  it("matches the utility planner without execution facts", () => {
    const options = [
      option("safe", 0.6, { risk: 0.1 }),
      option("bold", 0.9, { risk: 0.6 }),
    ];
    assert.equal(
      new ExecutionRiskPlanner().solve(problem(options)).actionId,
      new UtilityPlanner().solve(problem(options)).actionId,
    );
  });

  it("rejects a negative weight", () => {
    assert.throws(
      () => new ExecutionRiskPlanner(new UtilityModel(), { recovery: -1 }),
    );
  });
});
