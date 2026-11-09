import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  HumanAttentionPlanner,
  HumanAttentionBudget,
  UtilityPlanner,
  UtilityModel,
} from "../../../../src/index.ts";
import type { ActionOption, PlannerInput } from "../../../../src/index.ts";

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

describe("human-attention planning", () => {
  it("prefers low attention when utility is close", () => {
    const plan = new HumanAttentionPlanner().solve(
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
    assert.equal(plan.reasonCode, "human_attention_aware");
  });

  it("blocks a human option when the budget is gone", () => {
    const plan = new HumanAttentionPlanner().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          option("act", 0.6),
        ],
        { human_attention_budget: 0.2, human_attention_spent: 0.2 },
      ),
    );

    assert.equal(plan.actionId, "act");
  });

  it("waits when every option needs attention", () => {
    const plan = new HumanAttentionPlanner().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          { id: "guide", verb: "guide", name: "guide", expectedBenefit: 0.8 },
        ],
        { human_attention_budget: 0 },
      ),
    );

    assert.equal(plan.verb, "wait");
    assert.equal(plan.reasonCode, "human_attention_budget_exhausted");
  });

  it("counts approval as attention", () => {
    const plan = new HumanAttentionPlanner().solve(
      problem([
        option("direct", 0.7),
        option("approval", 0.75, { requiresApproval: true }),
      ]),
    );

    assert.equal(plan.actionId, "direct");
  });

  it("honors approval state", () => {
    const rejected = new HumanAttentionPlanner().solve(
      problem(
        [
          option("rejected", 0.9),
          option("direct", 0.6),
        ],
        { approvals: { rejected: "rejected" } },
      ),
    );
    assert.equal(rejected.actionId, "direct");

    const approved = new HumanAttentionPlanner().solve(
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
    const budget = new HumanAttentionBudget({ total: 1, spent: 0.9 });
    const plan = new HumanAttentionPlanner().solve(
      problem(
        [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          option("act", 0.6),
        ],
        { human_attention_budget: budget },
      ),
    );

    assert.equal(plan.actionId, "act");
    assert.equal(Math.round(budget.remaining() * 1e6) / 1e6, 0.1);
    assert.equal(budget.spend(0.1), 0);
    assert.equal(HumanAttentionBudget.fromDict(budget.toDict()).remaining(), 0);
  });

  it("matches the utility planner without attention facts", () => {
    const options = [
      option("safe", 0.6, { risk: 0.1 }),
      option("bold", 0.9, { risk: 0.6 }),
    ];
    assert.equal(
      new HumanAttentionPlanner().solve(problem(options)).actionId,
      new UtilityPlanner().solve(problem(options)).actionId,
    );
  });

  it("rejects a negative weight", () => {
    assert.throws(
      () => new HumanAttentionPlanner(new UtilityModel(), { interrupt: -1 }),
    );
  });
});
