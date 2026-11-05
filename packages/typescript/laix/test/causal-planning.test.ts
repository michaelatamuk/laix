import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CausalLedger,
  CommitmentLedger,
  PlanningPolicy,
  commitmentDue,
} from "../src/index.ts";
import type { DecisionRequest } from "../src/index.ts";

function request(at = "2026-11-01T10:00:00Z"): DecisionRequest {
  return { subject: "a task", at };
}

describe("causal ledger", () => {
  it("uses difference in means without propensities", () => {
    const ledger = new CausalLedger();
    ledger.add("d1", { arm: "ask", outcome: 1 });
    ledger.add("d2", { arm: "ask", outcome: 1 });
    ledger.add("d3", { arm: "wait", outcome: 0 });
    ledger.add("d4", { arm: "wait", outcome: 0 });

    const effect = ledger.effect("ask", "wait");
    assert.equal(effect.estimate, 1);
    assert.equal(effect.method, "difference-in-means");
  });

  it("uses inverse propensity weighting", () => {
    const ledger = new CausalLedger();
    ledger.add("d1", { arm: "ask", outcome: 1, propensity: 0.5 });
    ledger.add("d2", { arm: "wait", outcome: 0, propensity: 0.5 });

    const effect = ledger.effect("ask", "wait");
    assert.equal(effect.estimate, 2);
    assert.equal(effect.method, "inverse-propensity");
  });

  it("requires both arms", () => {
    const ledger = new CausalLedger();
    ledger.add("d1", { arm: "ask", outcome: 1 });
    assert.throws(() => ledger.effect("ask", "wait"), /both arms/);
  });
});

describe("commitments and planning", () => {
  it("orders commitments and respects dependencies", () => {
    const ledger = new CommitmentLedger([
      { id: "a", subject: "first", due: "2026-11-01T09:00:00Z" },
      {
        id: "b",
        subject: "second",
        due: "2026-11-01T11:00:00Z",
        dependsOn: ["a"],
      },
    ]);
    const now = new Date("2026-11-01T10:00:00Z");

    assert.equal(ledger.next(now)!.id, "a");
    assert.equal(ledger.blocked(ledger.get("b")), true);
    ledger.complete("a");
    assert.equal(ledger.blocked(ledger.get("b")), false);
    assert.equal(commitmentDue(ledger.get("b"), now), false);
  });

  it("acts on a due commitment and asks when blocked", () => {
    const ledger = new CommitmentLedger([
      { id: "a", subject: "first", due: "2026-11-01T09:00:00Z" },
    ]);
    const decision = new PlanningPolicy(ledger).decide(request())[0]!;

    assert.equal(decision.verb, "act");
    assert.equal(decision.reasonCode, "due_commitment");
    assert.equal(decision.actionId, "a");

    ledger.add({
      id: "a",
      subject: "first",
      due: "2026-11-01T09:00:00Z",
      dependsOn: ["missing"],
    });
    const blocked = new PlanningPolicy(ledger).decide(request())[0]!;
    assert.equal(blocked.verb, "ask");
    assert.equal(blocked.reasonCode, "blocked_commitment");
  });
});
