import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { RulePolicy, TargetedPolicy } from "../src/index.ts";

describe("policy authoring", () => {
  it("matches a threshold rule", () => {
    const policy = new RulePolicy([
      { when: { amount: { gte: 500 } }, verb: "ask", reasonCode: "over_limit" },
      { when: { priority: "high" }, verb: "act", reasonCode: "priority" },
    ]);
    const decision = policy.decide({
      subject: "a task",
      at: "2026-11-01T10:00:00Z",
      attributes: { amount: 780 },
    })[0]!;

    assert.equal(decision.verb, "ask");
    assert.equal(decision.reasonCode, "over_limit");
  });

  it("applies a target mode and recipients", () => {
    const policy = new TargetedPolicy(
      new RulePolicy([{ when: {}, verb: "guide", reasonCode: "share" }]),
      { target: "some", recipients: ["alice", "ben"] },
    );
    const decision = policy.decide({ subject: "a task", at: "2026-11-01T10:00:00Z" })[0]!;

    assert.equal(decision.target, "some");
    assert.deepEqual(decision.recipients, ["alice", "ben"]);
  });
});
