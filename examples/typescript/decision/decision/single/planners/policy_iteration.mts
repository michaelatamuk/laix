import {
  MdpModel,
  policyIteration,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const model = new MdpModel({
  states: ["s0", "s1", "s2"],
  actions: ["go", "stay"],
  transitions: [
    { state: "s0", action: "go", nextState: "s1", probability: 1, reward: 1 },
    { state: "s0", action: "stay", nextState: "s0", probability: 1, reward: 0 },
    { state: "s1", action: "go", nextState: "s2", probability: 1, reward: 2 },
    { state: "s1", action: "stay", nextState: "s1", probability: 1, reward: 0 },
  ],
  start: "s0",
  discount: 0.9,
  horizon: null,
});
const result = policyIteration(model);

console.log(
  result.policy.s0,
  result.policy.s1,
  Math.round(result.values.s0! * 1e6) / 1e6,
);
