import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { SignalAttentionLog, decideSignalAttention, isQuietHours } from "../../../src/index.ts";

describe("canonical attention policy", () => {
  it("uses guide as the canonical verb", () => {
    const [decision] = decideSignalAttention(
      { now: "2026-11-01T10:00:00+02:00", quietHours: null },
      [{ id: "a", kind: "kind-a", severity: "high", confidence: 0.9, due: "2026-11-02T09:00:00+02:00" }],
    );
    assert.equal(decision.verb, "guide");
    assert.equal(decision.reasonCode, "worth_surfacing");
  });

  it("passes quiet hours for a critical signal", () => {
    const [decision] = decideSignalAttention(
      { now: "2026-11-01T23:30:00+02:00", quietHours: "22:00-06:00" },
      [{ id: "b", kind: "kind-e", severity: "critical", confidence: 0.9 }],
    );
    assert.equal(decision.verb, "guide");
    assert.equal(decision.deliver, true);
  });

  it("treats the quiet-hours end as inclusive", () => {
    assert.equal(isQuietHours("2026-11-02T06:00:00+02:00", ["22:00", "06:00"]), true);
    assert.equal(isQuietHours("2026-11-02T06:01:00+02:00", ["22:00", "06:00"]), false);
  });

  it("keeps approval as a flag on a reversible action", () => {
    const [decision] = decideSignalAttention(
      { now: "2026-11-01T10:00:00+02:00", quietHours: null, allowAct: true },
      [
        {
          id: "c",
          kind: "kind-f",
          severity: "high",
          confidence: 0.9,
          reversible: true,
          requiresApproval: true,
          intent: { capability: "extend_licence", args: {} },
        },
      ],
    );
    assert.equal(decision.verb, "act");
    assert.equal(decision.reasonCode, "act");
    assert.equal(decision.requiresApproval, true);
    assert.equal(decision.undoHint, "cancel");
  });

  it("learns from outcomes", () => {
    const log = new SignalAttentionLog();
    assert.equal(log.adjustment("kind-a"), 0);
    log.record({ candidateId: "kind-a:1", verb: "guide", result: "helped", at: "2026-11-01T10:00:00Z" });
    assert.ok(log.adjustment("kind-a") > 0);
    assert.equal(log.acceptanceRate(), 1);
  });
});
