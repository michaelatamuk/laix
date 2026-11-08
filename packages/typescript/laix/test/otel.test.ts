import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { decisionAttributes } from "../src/index.ts";
import type { Decision } from "../src/index.ts";

describe("OpenTelemetry attributes", () => {
  it("maps the decision to stable names", () => {
    const decision: Decision = {
      verb: "act",
      confidence: 0.8,
      reasonCode: "safe_action",
      rationale: "inside the limit",
      decisionId: "DEC-1",
      traceId: "TRC-1",
      policyVersion: "live.v1",
      actionId: "valve",
      requiresApproval: true,
      score: 0.91,
      streamId: "stream-1",
      revision: 2,
      supersedes: "DEC-0",
    };

    const attributes = decisionAttributes(decision);

    assert.equal(attributes["laix.verb"], "act");
    assert.equal(attributes["laix.reason_code"], "safe_action");
    assert.equal(attributes["laix.decision.id"], "DEC-1");
    assert.equal(attributes["laix.trace.id"], "TRC-1");
    assert.equal(attributes["laix.policy.version"], "live.v1");
    assert.equal(attributes["laix.action.id"], "valve");
    assert.equal(attributes["laix.confidence"], 0.8);
    assert.equal(attributes["laix.approval.required"], true);
    assert.equal(attributes["laix.score"], 0.91);
    assert.equal(attributes["laix.stream.id"], "stream-1");
    assert.equal(attributes["laix.revision"], 2);
    assert.equal(attributes["laix.supersedes"], "DEC-0");
  });

  it("skips empty optional fields", () => {
    const attributes = decisionAttributes({
      verb: "wait",
      confidence: 0.5,
      reasonCode: "no_options",
      rationale: "nothing to do",
    });

    assert.equal("laix.decision.id" in attributes, false);
    assert.equal("laix.action.id" in attributes, false);
    assert.equal("laix.score" in attributes, false);
    assert.equal("laix.revision" in attributes, false);
  });
});
