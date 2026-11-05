import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  GroupPolicy,
  RulePolicy,
  ShadowPolicy,
  simulate,
} from "../src/index.ts";
import type { Decision, DecisionRequest } from "../src/index.ts";

function request(amount: number): DecisionRequest {
  return {
    subject: "a task",
    at: "2026-11-01T10:00:00Z",
    attributes: { amount },
  };
}

describe("group policy", () => {
  it("sets the target and masks private attributes", () => {
    const policy = new GroupPolicy(
      {
        decide: (): Decision[] => [
          {
            verb: "guide",
            confidence: 0.9,
            reasonCode: "share",
            rationale: "share",
            attributes: { topic: "math", health: "private" },
          },
        ],
      },
      {
        target: "all",
        recipients: ["alice", "ben", "chris"],
        privateAttributes: ["health"],
      },
    );
    const decision = policy.decide(request(1))[0]!;

    assert.equal(decision.target, "all");
    assert.deepEqual(decision.recipients, ["alice", "ben", "chris"]);
    assert.deepEqual(decision.attributes, { topic: "math" });
  });

  it("masks intent, alternatives, evidence and undo hints", () => {
    const policy = new GroupPolicy(
      {
        decide: (): Decision[] => [
          {
            verb: "guide",
            confidence: 0.9,
            reasonCode: "share",
            rationale: "private health",
            undoHint: "health record",
            evidence: [
              { id: "e1", kind: "note", source: "health" },
              { id: "e2", kind: "note", source: "catalog" },
            ],
            intent: { capability: "share", args: { health: "private", topic: "math" } },
            alternatives: [{ health: "private", ok: 1 }],
            attributes: {
              topic: "math",
              nested: { health: "private", visible: 1 },
            },
          },
        ],
      },
      {
        privateAttributes: ["health"],
        privateEvidence: ["health"],
        rationale: "shared summary",
        undoHint: "shared undo",
      },
    );
    const decision = policy.decide(request(1))[0]!;

    assert.equal(decision.rationale, "shared summary");
    assert.equal(decision.undoHint, "shared undo");
    assert.deepEqual(decision.evidence?.map((item) => item.id), ["e2"]);
    assert.deepEqual(decision.intent?.args, { topic: "math" });
    assert.deepEqual(decision.alternatives, [{ ok: 1 }]);
    assert.deepEqual(decision.attributes, {
      topic: "math",
      nested: { visible: 1 },
    });
  });
});

describe("policy simulation and shadow mode", () => {
  it("runs a policy offline", () => {
    const policy = new RulePolicy([
      { when: { amount: { gte: 500 } }, verb: "ask", reasonCode: "over_limit" },
    ]);
    const decisions = simulate(policy, [request(100), request(700)]);

    assert.deepEqual(
      decisions.map((item) => item[0]!.verb),
      ["wait", "ask"],
    );
  });

  it("returns the primary decision and records a disagreement", () => {
    const primary = new RulePolicy([
      { when: { amount: { gte: 500 } }, verb: "ask", reasonCode: "over_limit" },
    ]);
    const shadow = new RulePolicy([
      { when: { amount: { gte: 500 } }, verb: "act", reasonCode: "over_limit" },
    ]);
    const policy = new ShadowPolicy(primary, shadow);

    assert.equal(policy.decide(request(700))[0]!.verb, "ask");
    assert.equal(policy.differences.length, 1);
    assert.equal(policy.differences[0]!.shadow[0]!.verb, "act");
  });
});
