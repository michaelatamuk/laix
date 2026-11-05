import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readFileSync, rmSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  CausalLedger,
  CommitmentLedger,
  FileCommitmentStore,
  InMemoryCommitmentStore,
  PlanningPolicy,
  commitmentDue,
} from "../src/index.ts";
import type {
  Commitment,
  CommitmentFiles,
  DecisionRequest,
  Outcome,
} from "../src/index.ts";

const files: CommitmentFiles = {
  join: (directory, name) => join(directory, name),
  read: (path) => (existsSync(path) ? readFileSync(path, "utf8") : null),
  write: (path, text) => writeFileSync(path, text, "utf8"),
  remove: (path) => {
    if (existsSync(path)) unlinkSync(path);
  },
};

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

  it("adds outcomes and reports intervals and strata", () => {
    const outcomes: Outcome[] = [
      {
        id: "o1",
        decisionId: "d1",
        metric: "time",
        before: 10,
        after: 4,
        delta: -6,
        label: "helped",
        direction: "lower-better",
      },
      {
        id: "o2",
        decisionId: "d2",
        metric: "time",
        before: 10,
        after: 10,
        delta: 0,
        label: "neutral",
      },
    ];
    const ledger = CausalLedger.fromOutcomes(outcomes, { d1: "ask", d2: "wait" });
    const effect = ledger.effect("ask", "wait");

    assert.equal(effect.estimate, 6);
    assert.equal(effect.standardError, 0);
    assert.equal(effect.ciLow, 6);
    assert.equal(effect.ciHigh, 6);

    const stratified = new CausalLedger();
    stratified.add("a", { arm: "ask", outcome: 1, context: { stratum: "east" } });
    stratified.add("b", { arm: "wait", outcome: 0, context: { stratum: "east" } });
    stratified.add("c", { arm: "ask", outcome: 1, context: { stratum: "west" } });
    assert.deepEqual(Object.keys(stratified.effectByContext("ask", "wait")), ["east"]);
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

  it("skips a blocked commitment when a later one is ready", () => {
    const ledger = new CommitmentLedger([
      {
        id: "a",
        subject: "blocked first",
        due: "2026-11-01T09:00:00Z",
        dependsOn: ["missing"],
      },
      { id: "b", subject: "ready second", due: "2026-11-01T09:30:00Z" },
    ]);

    assert.deepEqual(ledger.blockedOpen().map((item) => item.id), ["a"]);
    assert.equal(ledger.nextActionable(new Date("2026-11-01T10:00:00Z"))!.id, "b");
    const decision = new PlanningPolicy(ledger).decide(request())[0]!;
    assert.equal(decision.verb, "act");
    assert.equal(decision.actionId, "b");
  });

  it("persists a commitment ledger", () => {
    const commitments: Commitment[] = [
      {
        id: "a",
        subject: "first",
        due: "2026-11-01T09:00:00Z",
        priority: 0.8,
        payload: { owner: "alice" },
      },
    ];
    const ledger = new CommitmentLedger(commitments);
    const memory = new InMemoryCommitmentStore();
    memory.save("task-1", ledger);
    assert.equal(memory.load("task-1")!.get("a").payload.owner, "alice");

    const directory = mkdtempSync(join(tmpdir(), "laix-commitments-"));
    try {
      const file = new FileCommitmentStore(directory, files);
      file.save("task-1", ledger);
      assert.equal(file.load("task-1")!.get("a").subject, "first");
      file.delete("task-1");
      assert.equal(file.load("task-1"), null);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });
});
