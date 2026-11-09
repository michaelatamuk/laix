import {
  ExecutionBridge,
} from "../../../../packages/typescript/laix/src/index.ts";
import type {
  ActionOption,
  Decision,
} from "../../../../packages/typescript/laix/src/index.ts";

const decision: Decision = {
  verb: "act",
  confidence: 0.9,
  reasonCode: "safe_action",
  rationale: "close the case",
  decisionId: "DEC-1",
  actionId: "close",
};
const action: ActionOption = { id: "close", verb: "act", name: "close case" };

let calls = 0;
const bridge = new ExecutionBridge({
  handlers: {
    "close case": () => {
      calls += 1;
      if (calls < 3) throw new Error("transient");
      return { closed: true };
    },
  },
});
const receipt = bridge.execute(decision, {
  action,
  actor: "agent",
  retry: { attempts: 3 },
});

const asyncBridge = new ExecutionBridge({
  asyncHandlers: {
    "close case": async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
      return { late: true };
    },
  },
});
const timeout = await asyncBridge.executeAsync(decision, {
  action,
  actor: "agent",
  timeoutMs: 5,
});

console.log(receipt.status, (receipt.detail as Record<string, unknown>).attempts, timeout.status);
