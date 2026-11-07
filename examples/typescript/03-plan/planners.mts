import {
  MDPPlanner,
  MdpModel,
  Simulator,
  UtilityPlanner,
  comparePlanners,
} from "../../../packages/typescript/laix/src/index.ts";
import type {
  DecisionEngine,
  DecisionProblem,
  Plan,
} from "../../../packages/typescript/laix/src/index.ts";

class FixedPlanner implements DecisionEngine {
  private readonly action: string;

  constructor(action: string) {
    this.action = action;
  }

  solve(_problem: DecisionProblem): Plan {
    return {
      verb: "act",
      confidence: 1,
      reasonCode: "fixed",
      rationale: `always ${this.action}`,
      actionId: this.action,
    };
  }
}

const utility = new UtilityPlanner().solve({
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options: [
    { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
    { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
  ],
  attributes: {},
});

const model = new MdpModel({
  states: ["s0", "s1"],
  actions: ["go", "stay"],
  transitions: [
    { state: "s0", action: "go", nextState: "s1", probability: 1, reward: 1 },
    { state: "s0", action: "stay", nextState: "s0", probability: 1, reward: 0 },
    { state: "s1", action: "go", nextState: "s1", probability: 1, reward: 2 },
  ],
  start: "s0",
  discount: 0.9,
  horizon: 2,
});
const mdp = new MDPPlanner(model).solve({
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options: [],
  attributes: {},
});

const simulator = new Simulator(
  (state, action) => [state, action === "right" ? 1 : 0],
  ["right", "wrong"],
  { start: "s", horizon: 4, name: "left-or-right" },
);
const report = comparePlanners(
  { right: new FixedPlanner("right"), wrong: new FixedPlanner("wrong") },
  [{ name: "left-or-right", simulator, optimum: 4 }],
);

console.log(
  utility.actionId,
  utility.score,
  mdp.actionId,
  mdp.score,
  report.best(),
  report.summary().right!.meanGap,
);
