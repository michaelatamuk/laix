import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  AttentionBudget,
  LiveDecisionEngine,
  defaultCases,
  runLiveBench,
} from "../../../src/index.ts";
import type { ActionOption, Commitment, DecisionProblem } from "../../../src/index.ts";

function problem(
  options: ActionOption[],
  attributes: Record<string, unknown> = {},
): DecisionProblem {
  return {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options,
    attributes,
  };
}

describe("integrated live planner", () => {
  it("combines promises, execution risk and attention", () => {
    const commitments: Commitment[] = [
      {
        id: "c1",
        subject: "send the report",
        due: "2026-11-01T09:00:00Z",
      },
    ];
    const plan = new LiveDecisionEngine().solve(
      problem(
        [
          {
            id: "fast",
            verb: "act",
            name: "fast",
            expectedBenefit: 1,
            reversible: false,
            interruptCost: 0.6,
            params: { commitments: { violates: ["c1"] } },
          },
          {
            id: "safe",
            verb: "act",
            name: "safe",
            expectedBenefit: 0.6,
            params: { commitments: { fulfills: ["c1"] } },
          },
        ],
        { commitments },
      ),
    );

    assert.equal(plan.actionId, "safe");
    assert.equal(plan.reasonCode, "live_decision");
    assert.deepEqual(plan.attributes?.commitments_fulfilled, ["c1"]);
    assert.equal(plan.attributes?.utility, 0.6);
  });

  it("blocks a rejected approval and respects the budget", () => {
    const rejected = new LiveDecisionEngine().solve(
      problem(
        [
          { id: "rejected", verb: "act", name: "rejected", expectedBenefit: 0.9 },
          { id: "direct", verb: "act", name: "direct", expectedBenefit: 0.6 },
        ],
        { approvals: { rejected: "rejected" } },
      ),
    );
    assert.equal(rejected.actionId, "direct");

    const budget = new LiveDecisionEngine().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          { id: "act", verb: "act", name: "act", expectedBenefit: 0.6 },
        ],
        { attention_budget: new AttentionBudget({ total: 1, spent: 0.9 }) },
      ),
    );
    assert.equal(budget.actionId, "act");
  });

  it("wins every benchmark case", () => {
    const report = runLiveBench(defaultCases(), {
      live: new LiveDecisionEngine(),
    });

    assert.equal(report.metrics[0]!.accuracy, 1);
    assert.equal(report.metrics[0]!.safetyViolations, 0);
  });

  it("waits when there are no options", () => {
    const plan = new LiveDecisionEngine().solve(problem([]));
    assert.equal(plan.verb, "wait");
    assert.equal(plan.reasonCode, "no_options");
  });
});
