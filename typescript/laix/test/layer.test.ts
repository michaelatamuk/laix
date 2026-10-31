import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { Layer } from "../src/index.ts";

describe("one layer entry point", () => {
  it("returns the same decision shape for an action request", () => {
    const layer = new Layer();
    const [decision] = layer.decide({
      subject: "one situation",
      at: "2026-11-01T10:00:00Z",
      situation: {
        id: "sit-1",
        at: "2026-11-01T10:00:00Z",
        subject: "one situation",
        beliefs: [{ confidence: 0.9 }],
        attributes: { urgency: 0.9 },
      },
      options: [
        { id: "a-wait", verb: "wait", name: "keep_observing", expectedBenefit: 0.2 },
        { id: "a-act", verb: "act", name: "apply_change", expectedBenefit: 0.9 },
      ],
    });
    assert.equal(decision.verb, "act");
    assert.equal(decision.reasonCode, "policy_rule");
    assert.equal(decision.actionId, "a-act");
  });

  it("observes when a cheap check can reduce uncertainty", () => {
    const layer = new Layer();
    const [decision] = layer.decide({
      subject: "one situation",
      at: "2026-11-01T10:00:00Z",
      situation: {
        id: "sit-2",
        at: "2026-11-01T10:00:00Z",
        subject: "one situation",
        beliefs: [{ confidence: 0.6 }],
        attributes: { urgency: 0.9, needs_more_info: true },
      },
      options: [
        { id: "a-wait", verb: "wait", name: "keep_observing" },
        { id: "a-observe", verb: "observe", name: "take_another_look", expectedBenefit: 0.6 },
        { id: "a-ask", verb: "ask", name: "ask_for_help" },
      ],
    });
    assert.equal(decision.verb, "observe");
    assert.equal(decision.actionId, "a-observe");
  });

  it("returns the same shape for an attention request", () => {
    const layer = new Layer();
    const [decision] = layer.decide({
      subject: "one signal",
      at: "2026-11-01T10:00:00Z",
      context: { now: "2026-11-01T10:00:00Z", quietHours: null },
      signals: [{ id: "s-1", kind: "k", severity: "high", confidence: 0.9 }],
    });
    assert.equal(decision.verb, "guide");
    assert.equal(decision.reasonCode, "worth_surfacing");
  });
});
