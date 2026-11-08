import {
  CAVODPlanner,
  PomdpModel,
  UtilityModel,
} from "../../../../../../packages/typescript/laix/src/index.ts";

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

console.log(plan.actionId, plan.attributes?.future_value, plan.attributes?.horizon);
