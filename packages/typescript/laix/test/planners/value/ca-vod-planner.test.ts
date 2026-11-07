import assert from "node:assert/strict";
import test from "node:test";

import { CAVODPlanner } from "../../../src/index.ts";
import type { PlannerInput } from "../../../src/index.ts";

function problem(): PlannerInput {
  return {
    subject: "invoice 4832",
    at: "2026-11-01T10:00:00Z",
    options: [
      {
        id: "pay",
        verb: "act",
        name: "pay the invoice",
        expectedBenefit: 0.95,
        risk: 0.05,
        requiresApproval: true,
        reversible: false,
        interruptCost: 0.6,
        params: { commitments: { violates: ["c1"] } },
      },
      {
        id: "ask",
        verb: "ask",
        name: "ask the owner",
        expectedBenefit: 0.6,
        interruptCost: 0.2,
        params: { commitments: { fulfills: ["c1"] } },
      },
      {
        id: "wait",
        verb: "wait",
        name: "wait",
        expectedBenefit: 0.2,
      },
    ],
    attributes: {
      commitments: [
        {
          id: "c1",
          subject: "ask the owner before paying",
          due: "2026-11-01T09:00:00Z",
        },
      ],
      human_attention_budget: { total: 2, spent: 0.5 },
      uncertainty: 0.8,
    },
  };
}

test("CA-VOD adds information value and chooses ask", () => {
  const plan = new CAVODPlanner().solve(problem());

  assert.equal(plan.verb, "ask");
  assert.equal(plan.actionId, "ask");
  assert.equal(plan.reasonCode, "value_of_decision");
  assert.equal(plan.attributes?.algorithm, "ca_vod.v1");
  assert.ok(Number(plan.attributes?.information_value) > 0);
  assert.equal(plan.attributes?.uncertainty, 0.8);
  assert.ok((plan.alternatives ?? []).length > 0);
});

test("CA-VOD waits when there are no options", () => {
  const plan = new CAVODPlanner().solve({
    subject: "empty",
    at: "2026-11-01T10:00:00Z",
    options: [],
    attributes: {},
  });

  assert.equal(plan.verb, "wait");
  assert.equal(plan.reasonCode, "no_options");
});
