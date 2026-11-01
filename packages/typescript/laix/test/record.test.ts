import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  approveRecord,
  createDecisionRecord,
  markExecuted,
  rejectRecord,
  undoRecord,
  verifyRecord,
} from "../src/index.ts";

const evidence = [
  {
    id: "e3",
    kind: "reference",
    quote: "The evidence is confirmed.",
    confidence: 0.95,
  },
];

function record() {
  return createDecisionRecord(
    {
      title: "One decision",
      decision: "Proceed with the plan.",
      confidence: 0.94,
      evidence,
      requiresApproval: true,
      metadata: { sourceRef: "ref-1" },
    },
    { now: "2026-11-04T10:00:00Z", id: "dr_test" },
  );
}

describe("decision record contract", () => {
  it("creates a draft with evidence and a fingerprint", () => {
    const draft = record();
    assert.equal(draft.status, "draft");
    assert.equal(draft.approval.state, "pending");
    assert.equal(draft.metadata.sourceRef, "ref-1");
    assert.equal(verifyRecord(draft), true);
  });

  it("requires evidence", () => {
    assert.throws(() => createDecisionRecord({ title: "No evidence", decision: "Do it", evidence: [] }), /evidence/i);
  });

  it("approves, audits and seals", () => {
    const approved = approveRecord(record(), { by: "owner", at: "2026-11-04T10:05:00Z" });
    assert.equal(approved.status, "approved");
    assert.ok(approved.audit.some((event) => event.action === "approved"));
    assert.equal(verifyRecord(approved), true);
  });

  it("detects tampering", () => {
    const approved = approveRecord(record(), { by: "owner" });
    const tampered = { ...approved, decision: { ...approved.decision, text: "Something else" } };
    assert.equal(verifyRecord(tampered), false);
  });

  it("rejects, executes and undoes", () => {
    assert.equal(rejectRecord(record(), { by: "owner" }).status, "rejected");
    const approved = approveRecord(record(), { by: "owner" });
    const executed = markExecuted(approved, { by: "operator" });
    assert.equal(executed.status, "executed");
    const undone = undoRecord(executed, { by: "owner" });
    assert.equal(undone.status, "undone");
  });
});
