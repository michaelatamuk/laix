import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  MDPEngine,
  MdpModel,
  Simulator,
  UtilityEngine,
  UtilityModel,
  actionValues,
  compareEngines,
  planActions,
  seededScenarios,
  toDecision,
  valueIteration,
} from "../src/index.ts";
import type {
  ActionOption,
  DecisionEngine,
  DecisionProblem,
  Plan,
  Scenario,
} from "../src/index.ts";

function mdp(): MdpModel {
  return new MdpModel({
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
    horizon: 2,
  });
}

function problem(attributes: Record<string, unknown> = {}): DecisionProblem {
  return {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options: [],
    attributes,
  };
}

class FixedEngine implements DecisionEngine {
  readonly action: string;

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

describe("utility engine", () => {
  it("chooses the highest expected utility", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
    ];
    const plan = new UtilityEngine().solve({ ...problem(), options });

    assert.equal(plan.actionId, "bold");
    assert.equal(plan.score, 0.75);
  });

  it("changes the choice under risk aversion", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.8, risk: 0.6 },
    ];
    const neutral = new UtilityEngine().solve({ ...problem(), options });
    const averse = new UtilityEngine(
      new UtilityModel({ riskAttitude: "averse" }),
    ).solve({ ...problem(), options });

    assert.equal(neutral.actionId, "bold");
    assert.equal(averse.actionId, "safe");
  });

  it("rejects an option outside a hard limit", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
    ];
    const plan = new UtilityEngine(new UtilityModel({ maxRisk: 0.4 })).solve({
      ...problem(),
      options,
    });

    assert.equal(plan.actionId, "safe");
    assert.equal(plan.alternatives?.[0]?.rejected_because, "outside the hard limits");
  });
});

describe("MDP engine", () => {
  it("computes values and action values", () => {
    const model = mdp();
    const values = valueIteration(model);

    assert.equal(values.s1, 2);
    assert.equal(values.s0, 2.8);
    assert.deepEqual(actionValues(model, "s0")[0], ["go", 2.8]);
  });

  it("returns the best action", () => {
    const plan = new MDPEngine(mdp()).solve(problem({ state: "s0" }));

    assert.equal(plan.actionId, "go");
    assert.equal(plan.score, 2.8);
    assert.equal(plan.alternatives?.[0]?.action_id, "stay");
  });

  it("honours the horizon", () => {
    const plan = new MDPEngine(mdp()).solve(problem());
    const short = new MDPEngine(
      new MdpModel({
        states: ["s0", "s1", "s2"],
        actions: ["go", "stay"],
        transitions: [
          { state: "s0", action: "go", nextState: "s1", reward: 1 },
          { state: "s0", action: "stay", nextState: "s0", reward: 0 },
          { state: "s1", action: "go", nextState: "s2", reward: 2 },
          { state: "s1", action: "stay", nextState: "s1", reward: 0 },
        ],
        start: "s0",
        horizon: 1,
      }),
    ).solve(problem());

    assert.equal(plan.score, 2.8);
    assert.equal(short.score, 1);
  });

  it("follows the greedy plan", () => {
    assert.deepEqual(planActions(mdp()), ["s0:go", "s1:go"]);
  });
});

describe("engine simulator", () => {
  function scenario(horizon = 4): Scenario {
    const simulator = new Simulator(
      (state, action) => [state, action === "right" ? 1 : 0],
      ["right", "wrong"],
      { start: "s", horizon, name: "left-or-right" },
    );
    return { name: "left-or-right", simulator, optimum: horizon };
  }

  it("compares engines and reports the gap", () => {
    const report = compareEngines(
      { right: new FixedEngine("right"), wrong: new FixedEngine("wrong") },
      [scenario(4)],
    );
    const summary = report.summary();

    assert.equal(report.best(), "right");
    assert.equal(summary.right!.meanReward, 4);
    assert.equal(summary.right!.meanGap, 0);
    assert.equal(summary.wrong!.meanGap, 1);
  });

  it("runs the planner in an MDP simulator", () => {
    const model = mdp();
    const result = Simulator.fromMdp(model).run(new MDPEngine(model));

    assert.equal(result.totalReward, 3);
    assert.deepEqual(result.steps.map((item) => item.action), ["go", "go"]);
  });

  it("builds repeatable seeded scenarios", () => {
    const first = seededScenarios(7, { count: 2, horizon: 3 });
    const second = seededScenarios(7, { count: 2, horizon: 3 });

    assert.deepEqual(
      first.map((item) => item.name),
      second.map((item) => item.name),
    );
    assert.deepEqual(
      first.map((item) => item.optimum),
      second.map((item) => item.optimum),
    );
    assert.equal(
      compareEngines({ a: new FixedEngine("a") }, first).best(),
      "a",
    );
  });
});

describe("engine helper", () => {
  it("turns a plan into one decision", () => {
    const decision = toDecision(
      {
        verb: "act",
        confidence: 0.9,
        reasonCode: "best_plan",
        rationale: "the best plan",
        actionId: "a1",
      },
      { subject: "a task", at: "2026-11-01T10:00:00Z", attributes: { urgency: 0.8 } },
      { policyVersion: "utility.v1" },
    );

    assert.equal(decision.actionId, "a1");
    assert.deepEqual(decision.attributes, { urgency: 0.8 });
    assert.equal(decision.policyVersion, "utility.v1");
  });
});
