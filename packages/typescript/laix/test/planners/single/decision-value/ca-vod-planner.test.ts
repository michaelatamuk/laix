import assert from "node:assert/strict";
import test from "node:test";

import { CAVODPlanner, PomdpModel, UtilityModel } from "../../../../src/index.ts";
import type { PlannerInput } from "../../../../src/index.ts";

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

test("CA-VOD uses belief-state future value", () => {
  const model = new PomdpModel({
    states: ["safe", "risky"],
    actions: ["act", "ask", "wait"],
    observations: ["ok", "good", "bad"],
    transitions: [
      { state: "safe", action: "act", nextState: "safe", reward: 1 },
      { state: "risky", action: "act", nextState: "risky", reward: -1 },
      { state: "safe", action: "ask", nextState: "safe", reward: 0 },
      { state: "risky", action: "ask", nextState: "risky", reward: 0 },
      { state: "safe", action: "wait", nextState: "safe", reward: 0 },
      { state: "risky", action: "wait", nextState: "risky", reward: 0 },
    ],
    observationTable: [
      { nextState: "safe", action: "act", observation: "ok", probability: 1 },
      { nextState: "risky", action: "act", observation: "ok", probability: 1 },
      { nextState: "safe", action: "ask", observation: "good", probability: 1 },
      { nextState: "risky", action: "ask", observation: "bad", probability: 1 },
      { nextState: "safe", action: "wait", observation: "ok", probability: 1 },
      { nextState: "risky", action: "wait", observation: "ok", probability: 1 },
    ],
    discount: 0.9,
    horizon: 2,
  });
  const plan = new CAVODPlanner(new UtilityModel(), {
    pomdpModel: model,
    belief: { safe: 0.5, risky: 0.5 },
  }).solve({
    subject: "belief",
    at: "2026-11-01T10:00:00Z",
    options: [
      { id: "act", verb: "act", name: "act", expectedBenefit: 0.55 },
      { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.2 },
      { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.1 },
    ],
    attributes: {},
  });

  assert.equal(plan.actionId, "ask");
  assert.ok(Number(plan.attributes?.future_value) > 0);
  assert.equal(plan.attributes?.horizon, 2);
});
