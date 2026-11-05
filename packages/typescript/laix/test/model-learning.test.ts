import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ModelLearner, valueIteration } from "../src/index.ts";

describe("model learner", () => {
  it("estimates transitions and reward", () => {
    const learner = new ModelLearner({ prior: 0.5 });
    learner.observe("s0", "go", "s1", 1);
    learner.observe("s0", "go", "s1", 1);
    learner.observe("s0", "go", "s0", 0);

    assert.deepEqual(learner.transitionProbabilities("s0", "go"), {
      s0: 0.375,
      s1: 0.625,
    });
    assert.equal(learner.expectedReward("s0", "go"), 0.666667);
    assert.equal(learner.learned()[0]!.count, 3);
  });

  it("rolls back a worse model", () => {
    const learner = new ModelLearner({ prior: 0.5 });
    learner.observe("s0", "go", "s1", 1);
    const validation: Array<[string, string, string, number]> = [
      ["s0", "go", "s1", 1],
    ];

    assert.equal(learner.commit(validation), true);
    const best = learner.bestScore;
    learner.observe("s0", "go", "s0", -1);
    assert.equal(learner.commit(validation), false);
    assert.equal(learner.bestScore, best);
    assert.deepEqual(learner.transitionProbabilities("s0", "go"), { s1: 1 });
    assert.equal(learner.history.at(-1)![1], false);
  });

  it("round trips a JSON snapshot", () => {
    const learner = new ModelLearner();
    learner.observe("s0", "go", "s1", 2);
    const snapshot = learner.snapshot();
    const parsed = JSON.parse(JSON.stringify(snapshot)) as Record<string, unknown>;

    const restored = new ModelLearner();
    restored.restore(parsed);

    assert.deepEqual(restored.transitionProbabilities("s0", "go"), { s1: 1 });
    assert.equal(restored.expectedReward("s0", "go"), 2);
  });

  it("exports a learned MDP", () => {
    const learner = new ModelLearner();
    learner.observe("s0", "go", "s1", 1);
    learner.observe("s1", "go", "s1", 2);
    const model = learner.toMdpModel({ start: "s0", horizon: 2 });

    assert.equal(valueIteration(model).s0, 2.8);
  });
});
