import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  MDPPlanner,
  MdpModel,
  Simulator,
  UtilityPlanner,
  UtilityModel,
  actionValues,
  comparePlanners,
  planActions,
  runPlannerBench,
  seededScenarios,
  toDecision,
  valueIteration,
} from "../src/index.ts";
import type {
  ActionOption,
  Planner,
  PlannerInput,
  PlannerResult,
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

function problem(attributes: Record<string, unknown> = {}): PlannerInput {
  return {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options: [],
    attributes,
  };
}

class FixedPlanner implements Planner {
  readonly action: string;

  constructor(action: string) {
    this.action = action;
  }

  solve(_problem: PlannerInput): PlannerResult {
    return {
      verb: "act",
      confidence: 1,
      reasonCode: "fixed",
      rationale: `always ${this.action}`,
      actionId: this.action,
    };
  }
}

describe("utility planner", () => {
  it("chooses the highest expected utility", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
    ];
    const plan = new UtilityPlanner().solve({ ...problem(), options });

    assert.equal(plan.actionId, "bold");
    assert.equal(plan.score, 0.75);
  });

  it("changes the choice under risk aversion", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.8, risk: 0.6 },
    ];
    const neutral = new UtilityPlanner().solve({ ...problem(), options });
    const averse = new UtilityPlanner(
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
    const plan = new UtilityPlanner(new UtilityModel({ maxRisk: 0.4 })).solve({
      ...problem(),
      options,
    });

    assert.equal(plan.actionId, "safe");
    assert.equal(plan.alternatives?.[0]?.rejected_because, "outside the hard limits");
  });

  it("enforces Situation constraints and approval", () => {
    const options: ActionOption[] = [
      { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
    ];
    const plan = new UtilityPlanner().solve({
      ...problem(),
      situation: {
        id: "sit-1",
        at: "2026-11-01T10:00:00Z",
        subject: "leak",
        constraints: [{ kind: "risk", value: 0.2, hard: true }],
      },
      options,
    });

    assert.equal(plan.actionId, "safe");
    assert.equal(plan.alternatives?.[0]?.rejected_because, "blocked by risk:risk");

    const approval = new UtilityPlanner().solve({
      ...problem(),
      situation: {
        id: "sit-2",
        at: "2026-11-01T10:00:00Z",
        subject: "payment",
        constraints: [{ kind: "approval", value: true, hard: true }],
      },
      options: [{ id: "pay", verb: "act", name: "pay" }],
    });
    assert.equal(approval.requiresApproval, true);
  });
});

describe("MDP planner", () => {
  it("computes values and action values", () => {
    const model = mdp();
    const values = valueIteration(model);

    assert.equal(values.s1, 2);
    assert.equal(values.s0, 2.8);
    assert.deepEqual(actionValues(model, "s0")[0], ["go", 2.8]);
  });

  it("returns the best action", () => {
    const plan = new MDPPlanner(mdp()).solve(problem({ state: "s0" }));

    assert.equal(plan.actionId, "go");
    assert.equal(plan.score, 2.8);
    assert.equal(plan.alternatives?.[0]?.action_id, "stay");
  });

  it("honours the horizon", () => {
    const plan = new MDPPlanner(mdp()).solve(problem());
    const short = new MDPPlanner(
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

describe("planner simulator", () => {
  function scenario(horizon = 4): Scenario {
    const simulator = new Simulator(
      (state, action) => [state, action === "right" ? 1 : 0],
      ["right", "wrong"],
      { start: "s", horizon, name: "left-or-right" },
    );
    return { name: "left-or-right", simulator, optimum: horizon };
  }

  it("compares planners and reports the gap", () => {
    const report = comparePlanners(
      { right: new FixedPlanner("right"), wrong: new FixedPlanner("wrong") },
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
    const result = Simulator.fromMdp(model).run(new MDPPlanner(model));

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
      comparePlanners({ a: new FixedPlanner("a") }, first).best(),
      "a",
    );
  });

  it("runs repeatable stochastic MDP simulations", () => {
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
    const simulator = Simulator.fromMdp(model, { seed: 7 });
    const first = simulator.run(new FixedPlanner("go"));
    const second = simulator.run(new FixedPlanner("go"));

    assert.deepEqual(first, second);
    assert.ok(["s1", "s2"].includes(first.finalState));
    const endings = new Set(
      Array.from({ length: 20 }, (_, seed) =>
        Simulator.fromMdp(model, { seed: seed + 1 }).run(new FixedPlanner("go")).finalState,
      ),
    );
    assert.deepEqual([...endings].sort(), ["s1", "s2"]);
  });

  it("runs the planner bench", () => {
    const report = runPlannerBench();
    const summary = report.summary();

    assert.equal(summary.mdp!.meanReward, 4);
    assert.equal(summary.mdp!.meanGap, 0);
    assert.equal(summary["stay-baseline"]!.meanGap, 1);
    assert.equal(report.best(), "mdp");
  });
});

describe("planner helper", () => {
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
