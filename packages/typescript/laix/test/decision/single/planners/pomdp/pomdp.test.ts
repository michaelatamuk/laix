import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  MdpModel,
  POMDPPlanner,
  PomdpModel,
  beliefEntropy,
  beliefFromState,
  beliefUpdate,
  comparePomdpToMdp,
  observationProbability,
  pomdpValue,
  valueIteration,
} from "../../../../../src/index.ts";
import type { PlannerInput } from "../../../../../src/index.ts";

function model(): PomdpModel {
  return new PomdpModel({
    states: ["s0", "s1"],
    actions: ["go", "stay"],
    observations: ["o0", "o1"],
    transitions: [
      { state: "s0", action: "go", nextState: "s1", probability: 1, reward: 1 },
      { state: "s0", action: "stay", nextState: "s0", probability: 1, reward: 0 },
      { state: "s1", action: "go", nextState: "s1", probability: 1, reward: 2 },
      { state: "s1", action: "stay", nextState: "s1", probability: 1, reward: 0 },
    ],
    observationTable: [
      { nextState: "s0", action: "go", observation: "o0", probability: 1 },
      { nextState: "s0", action: "stay", observation: "o0", probability: 1 },
      { nextState: "s1", action: "go", observation: "o1", probability: 1 },
      { nextState: "s1", action: "stay", observation: "o1", probability: 1 },
    ],
    discount: 0.9,
    horizon: 1,
  });
}

function problem(attributes: Record<string, unknown> = {}): PlannerInput {
  return {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options: [],
    attributes,
  };
}

describe("POMDP", () => {
  it("updates a belief", () => {
    const belief = beliefFromState("s0", ["s0", "s1"]);
    assert.deepEqual(beliefUpdate(model(), belief, "go", "o1"), { s1: 1 });
    assert.equal(observationProbability(model(), belief, "go", "o1"), 1);
    assert.equal(beliefEntropy({ s0: 0.5, s1: 0.5 }), 1);
  });

  it("plans under a belief", () => {
    const pomdp = model();
    const belief = beliefFromState("s0", pomdp.states);
    assert.equal(pomdpValue(pomdp, belief), 1);

    const plan = new POMDPPlanner(pomdp).solve(problem({ belief }));
    assert.equal(plan.actionId, "go");
    assert.equal(plan.score, 1);
    assert.equal(plan.attributes?.entropy, 0);
  });

  it("defaults to a uniform belief", () => {
    const plan = new POMDPPlanner(model()).solve(problem());
    assert.equal(plan.actionId, "go");
    assert.deepEqual(plan.attributes?.belief, { s0: 0.5, s1: 0.5 });
  });

  it("requires observations for every reachable pair", () => {
    assert.throws(
      () =>
        new PomdpModel({
          states: ["s0", "s1"],
          actions: ["go"],
          observations: ["o0", "o1"],
          transitions: [{ state: "s0", action: "go", nextState: "s1", reward: 1 }],
          observationTable: [],
        }),
      /missing observations/,
    );
  });

  it("compares with the MDP path", () => {
    const pomdp = model();
    const mdp = new MdpModel({
      states: ["s0", "s1"],
      actions: ["go", "stay"],
      transitions: [
        { state: "s0", action: "go", nextState: "s1", reward: 1 },
        { state: "s0", action: "stay", nextState: "s0", reward: 0 },
        { state: "s1", action: "go", nextState: "s1", reward: 2 },
        { state: "s1", action: "stay", nextState: "s1", reward: 0 },
      ],
      start: "s0",
      discount: 0.9,
      horizon: 2,
    });
    const belief = beliefFromState("s0", pomdp.states);
    const comparison = comparePomdpToMdp(pomdp, mdp, belief, { horizon: 2 });

    assert.equal(comparison.state, "s0");
    assert.equal(comparison.pomdp, comparison.mdp);
    assert.equal(comparison.pomdp, valueIteration(mdp).s0);
  });
});
