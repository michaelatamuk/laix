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
});
