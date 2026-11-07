import {
  POMDPPlanner,
  PomdpModel,
  beliefFromState,
} from "../../../packages/typescript/laix/src/index.ts";

const model = new PomdpModel({
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
  horizon: 2,
});
const plan = new POMDPPlanner(model).solve({
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options: [],
  attributes: { belief: beliefFromState("s0", model.states) },
});
console.log(plan.verb, plan.actionId, plan.score);
