/** Utility constraints, stochastic simulation and POMDP comparison. */

import {
  MDPEngine,
  MdpModel,
  POMDPEngine,
  PomdpModel,
  Simulator,
  UtilityEngine,
  beliefFromState,
  comparePomdpToMdp,
} from "../../../packages/typescript/laix/src/index.ts";
import type { DecisionEngine, DecisionProblem, Plan } from "../../../packages/typescript/laix/src/index.ts";

class AlwaysGo implements DecisionEngine {
  solve(_problem: DecisionProblem): Plan {
    return {
      verb: "act",
      confidence: 1,
      reasonCode: "fixed",
      rationale: "always go",
      actionId: "go",
    };
  }
}

const utility = new UtilityEngine().solve({
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  situation: {
    id: "sit-1",
    at: "2026-11-01T10:00:00Z",
    subject: "leak",
    constraints: [{ id: "risk-limit", kind: "risk", value: 0.2, hard: true }],
  },
  options: [
    { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
    { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
  ],
  attributes: {},
});
console.log(utility.actionId, utility.alternatives?.[0]?.rejected_because);

const model = new MdpModel({
  states: ["s0", "s1", "s2"],
  actions: ["go"],
  transitions: [
    { state: "s0", action: "go", nextState: "s1", probability: 0.5, reward: 1 },
    { state: "s0", action: "go", nextState: "s2", probability: 0.5, reward: 2 },
  ],
  start: "s0",
  horizon: 1,
});
const result = Simulator.fromMdp(model, { seed: 7 }).run(new AlwaysGo());
console.log(result.finalState, result.totalReward);

const pomdp = new PomdpModel({
  states: ["s0", "s1"],
  actions: ["go", "stay"],
  observations: ["o0", "o1"],
  transitions: [
    { state: "s0", action: "go", nextState: "s1", reward: 1 },
    { state: "s0", action: "stay", nextState: "s0", reward: 0 },
    { state: "s1", action: "go", nextState: "s1", reward: 2 },
    { state: "s1", action: "stay", nextState: "s1", reward: 0 },
  ],
  observationTable: [
    { nextState: "s0", action: "go", observation: "o0" },
    { nextState: "s0", action: "stay", observation: "o0" },
    { nextState: "s1", action: "go", observation: "o1" },
    { nextState: "s1", action: "stay", observation: "o1" },
  ],
  discount: 0.9,
  horizon: 1,
});
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
  horizon: 1,
});
const belief = beliefFromState("s0", pomdp.states);
const comparison = comparePomdpToMdp(pomdp, mdp, belief, { horizon: 1 });
const plan = new POMDPEngine(pomdp).solve({
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options: [],
  attributes: { belief },
});
console.log(comparison.state, comparison.gap, plan.actionId);
