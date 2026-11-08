import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ExecutionBridge } from "../src/index.ts";
import type { ActionOption, Decision } from "../src/index.ts";

const decision: Decision = {
  verb: "act",
  confidence: 0.9,
  reasonCode: "test",
  rationale: "test",
  decisionId: "DEC-1",
  actionId: "pay",
};

const action: ActionOption = { id: "pay", verb: "act", name: "pay" };

describe("execution integrity", () => {
  it("runs the handler once per idempotency key", () => {
    let calls = 0;
    const bridge = new ExecutionBridge({
      handlers: {
        pay: () => {
          calls += 1;
          return { ok: true };
        },
      },
    });

    const first = bridge.execute(decision, { action, actor: "agent", idempotencyKey: "K-1" });
    const second = bridge.execute(decision, { action, actor: "agent", idempotencyKey: "K-1" });

    assert.equal(first.status, "executed");
    assert.equal(second.status, "duplicate");
    assert.equal((second.detail as Record<string, unknown>).original, first.id);
    assert.equal(calls, 1);
  });

  it("reconciles an unknown outcome", () => {
    const bridge = new ExecutionBridge({ handlers: { pay: () => ({ ok: true }) } });
    const executed = bridge.execute(decision, { action, actor: "agent", idempotencyKey: "K-2" });
    const unknown = bridge.markUnknown(executed.id, { actor: "agent", reason: "response lost" });

    assert.equal(unknown.status, "unknown");
    const reconciled = bridge.reconcile(unknown.id, {
      actor: "agent",
      status: "executed",
      detail: { confirmed: true },
    });
    assert.equal(reconciled.status, "executed");
    assert.equal(reconciled.idempotencyKey, "K-2");
  });

  it("maps action names to execution status", () => {
    const bridge = new ExecutionBridge({ handlers: { pay: () => ({ ok: true }) } });
    const executed = bridge.execute(decision, { action, actor: "agent" });
    bridge.markUnknown(executed.id, { actor: "agent", reason: "response lost" });

    assert.deepEqual(bridge.executionState(), { pay: "unknown" });
  });

  it("retries a transient handler failure", () => {
    let calls = 0;
    const bridge = new ExecutionBridge({
      handlers: {
        pay: () => {
          calls += 1;
          if (calls < 3) throw new Error("transient");
          return { ok: true };
        },
      },
    });

    const receipt = bridge.execute(decision, {
      action,
      actor: "agent",
      retry: { attempts: 3 },
    });

    assert.equal(receipt.status, "executed");
    assert.deepEqual(receipt.detail, { ok: true, attempts: 3 });
    assert.equal(calls, 3);
  });

  it("stops after the retry budget", () => {
    let calls = 0;
    const bridge = new ExecutionBridge({
      handlers: {
        pay: () => {
          calls += 1;
          throw new Error("still broken");
        },
      },
    });

    const receipt = bridge.execute(decision, {
      action,
      actor: "agent",
      retry: { attempts: 2 },
    });

    assert.equal(receipt.status, "failed");
    assert.equal((receipt.detail as Record<string, unknown>).attempts, 2);
    assert.match(receipt.error ?? "", /still broken/);
    assert.equal(calls, 2);
  });
});
