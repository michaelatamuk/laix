import assert from "node:assert/strict";
import test from "node:test";

import {
  CABBPlanner,
  HumanAttentionBudget,
  ReplanPlanner,
  RolloutPlanner,
  planDecisions,
  replanDecisions,
  rolloutDecisions,
} from "../../../src/index.ts";
import type { DecisionScenario } from "../../../src/index.ts";

function scenario(): DecisionScenario {
  return {
    steps: [
      {
        at: "2026-11-01T10:00:00Z",
        options: [
          {
            id: "pay",
            verb: "act",
            name: "pay",
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
            name: "ask",
            expectedBenefit: 0.6,
            interruptCost: 0.2,
            params: { commitments: { fulfills: ["c1"] } },
          },
        ],
      },
      {
        at: "2026-11-01T11:00:00Z",
        options: [
          { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.2 },
          { id: "verify", verb: "verify", name: "verify", expectedBenefit: 0.4 },
        ],
      },
    ],
    commitments: [
      {
        id: "c1",
        subject: "ask before paying",
        due: "2026-11-01T09:00:00Z",
      },
    ],
    humanAttentionBudget: new HumanAttentionBudget({ total: 2, spent: 0.5 }),
  };
}

function greedyTrap(): DecisionScenario {
  return {
    steps: [
      {
        at: "2026-11-01T10:00:00Z",
        options: [{ id: "start", verb: "wait", name: "start", expectedBenefit: 0.0 }],
      },
      {
        at: "2026-11-01T10:10:00Z",
        options: [
          { id: "big", verb: "act", name: "big", expectedBenefit: 1.0, interruptCost: 0.9 },
          { id: "small", verb: "act", name: "small", expectedBenefit: 0.6, interruptCost: 0.3 },
        ],
      },
      {
        at: "2026-11-01T10:20:00Z",
        options: [
          { id: "bonus", verb: "act", name: "bonus", expectedBenefit: 1.0, interruptCost: 0.6 },
          { id: "nothing", verb: "wait", name: "nothing", expectedBenefit: 0.1 },
        ],
      },
    ],
    humanAttentionBudget: new HumanAttentionBudget({ total: 1, spent: 0 }),
  };
}

test("CABB keeps the commitment first", () => {
  const plan = new CABBPlanner().plan(scenario());

  assert.equal(plan.actions[0], "ask");
  assert.equal(plan.actions.length, 2);
  assert.deepEqual(plan.violations, []);
  assert.ok(plan.attentionSpent <= 1.5);
  assert.ok(plan.nodes > 0);
  assert.equal(plan.optimal, true);
});

test("CABB handles an empty scenario", () => {
  const plan = planDecisions({ steps: [] });

  assert.deepEqual(plan.actions, []);
  assert.equal(plan.score, 0);
  assert.equal(plan.optimal, true);
});

test("rollout keeps the commitment first without claiming optimality", () => {
  const plan = new RolloutPlanner().plan(scenario());

  assert.equal(plan.actions[0], "ask");
  assert.equal(plan.actions.length, 2);
  assert.equal(plan.optimal, false);
});

test("rollout handles an empty scenario", () => {
  const plan = rolloutDecisions({ steps: [] });

  assert.deepEqual(plan.actions, []);
  assert.equal(plan.score, 0);
});

test("replan rebuilds the remaining chain", () => {
  const result = new ReplanPlanner().replan(scenario(), ["ask"]);

  assert.deepEqual(result.executed, ["ask"]);
  assert.deepEqual(result.actions, ["verify"]);
  assert.equal(result.optimal, true);
  assert.ok(result.reason.startsWith("replanned"));
});

test("replan reports when nothing is left", () => {
  const result = replanDecisions(scenario(), ["ask", "verify"]);

  assert.deepEqual(result.actions, []);
  assert.equal(result.reason, "nothing left to replan");
});

test("CABB beats greedy rollout on an attention tradeoff", () => {
  const exact = new CABBPlanner().plan(greedyTrap());
  const greedy = new RolloutPlanner().plan(greedyTrap());

  assert.deepEqual(exact.actions, ["start", "small", "bonus"]);
  assert.deepEqual(greedy.actions, ["start", "big", "nothing"]);
  assert.ok(exact.score > greedy.score);
});
