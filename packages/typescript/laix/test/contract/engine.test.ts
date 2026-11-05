import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { EnginePolicy } from "../../src/index.ts";
import type { DecisionProblem, Plan } from "../../src/index.ts";

class FakeEngine {
  solve(problem: DecisionProblem): Plan {
    assert.equal(problem.subject, "a task");
    assert.equal(problem.options[0]!.id, "a1");
    return {
      verb: "act",
      confidence: 0.91,
      reasonCode: "best_plan",
      rationale: "the engine selected the best option",
      actionId: "a1",
      intent: { capability: "apply", args: { id: "a1" } },
      requiresApproval: true,
      reversible: true,
      score: 0.91,
      alternatives: [{ id: "a2", score: 0.4 }],
    };
  }
}

describe("engine policy", () => {
  it("returns the one decision shape", () => {
    const policy = new EnginePolicy(new FakeEngine(), "fake-engine.v1");
    const decision = policy.decide({
      subject: "a task",
      at: "2026-11-01T10:00:00Z",
      options: [{ id: "a1", verb: "act", name: "apply" }],
    })[0]!;

    assert.equal(decision.verb, "act");
    assert.equal(decision.actionId, "a1");
    assert.equal(decision.requiresApproval, true);
    assert.equal(decision.reversible, true);
    assert.equal(decision.policyVersion, "fake-engine.v1");
    assert.deepEqual(decision.intent, { capability: "apply", args: { id: "a1" } });
  });
});
