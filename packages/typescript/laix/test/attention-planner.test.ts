import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  AttentionAwareEngine,
  AttentionBudget,
  UtilityEngine,
  UtilityModel,
} from "../src/index.ts";
import type { ActionOption, DecisionProblem } from "../src/index.ts";

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

function option(
  id: string,
  benefit: number,
  extra: Record<string, unknown> = {},
): ActionOption {
  return { id, verb: "act", name: id, expectedBenefit: benefit, ...extra };
}

describe("attention-aware planning", () => {
  it("prefers low attention when utility is close", () => {
    const plan = new AttentionAwareEngine().solve(
      problem([
        option("direct", 0.7),
        {
          id: "guide",
          verb: "guide",
          name: "guide",
          expectedBenefit: 0.75,
          interruptCost: 0.8,
        },
      ]),
    );

    assert.equal(plan.actionId, "direct");
    assert.equal(plan.reasonCode, "attention_aware");
  });

  it("blocks a human option when the budget is gone", () => {
    const plan = new AttentionAwareEngine().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          option("act", 0.6),
        ],
        { attention_budget: 0.2, attention_spent: 0.2 },
      ),
    );

    assert.equal(plan.actionId, "act");
  });

  it("waits when every option needs attention", () => {
    const plan = new AttentionAwareEngine().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          { id: "guide", verb: "guide", name: "guide", expectedBenefit: 0.8 },
        ],
        { attention_budget: 0 },
      ),
    );

    assert.equal(plan.verb, "wait");
    assert.equal(plan.reasonCode, "attention_budget_exhausted");
  });

  it("counts approval as attention", () => {
    const plan = new AttentionAwareEngine().solve(
      problem([
        option("direct", 0.7),
        option("approval", 0.75, { requiresApproval: true }),
      ]),
    );

    assert.equal(plan.actionId, "direct");
  });

  it("honors approval state", () => {
    const rejected = new AttentionAwareEngine().solve(
      problem(
        [
          option("rejected", 0.9),
          option("direct", 0.6),
        ],
        { approvals: { rejected: "rejected" } },
      ),
    );
    assert.equal(rejected.actionId, "direct");

    const approved = new AttentionAwareEngine().solve(
      problem(
        [
          option("direct", 0.7),
          option("approved", 0.75, { requiresApproval: true }),
        ],
        { approvals: { approved: "approved" } },
      ),
    );
    assert.equal(approved.actionId, "approved");
  });

  it("shares an attention budget object", () => {
    const budget = new AttentionBudget({ total: 1, spent: 0.9 });
    const plan = new AttentionAwareEngine().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          option("act", 0.6),
        ],
        { attention_budget: budget },
      ),
    );

    assert.equal(plan.actionId, "act");
    assert.equal(Math.round(budget.remaining() * 1e6) / 1e6, 0.1);
    assert.equal(budget.spend(0.1), 0);
  });

  it("matches the utility engine without attention facts", () => {
    const options = [
      option("safe", 0.6, { risk: 0.1 }),
      option("bold", 0.9, { risk: 0.6 }),
    ];
    assert.equal(
      new AttentionAwareEngine().solve(problem(options)).actionId,
      new UtilityEngine().solve(problem(options)).actionId,
    );
  });

  it("rejects a negative weight", () => {
    assert.throws(
      () => new AttentionAwareEngine(new UtilityModel(), { interrupt: -1 }),
    );
  });
});
