import { ExecutionBridge } from "../../../packages/typescript/laix/src/index.ts";

const bridge = new ExecutionBridge({
  handlers: {
    reserve: () => ({ reserved: true }),
    charge: () => {
      throw new Error("declined");
    },
  },
  undoHandlers: {
    reserve: () => ({ released: true }),
  },
});
const result = bridge.runSteps(
  [
    { action: { id: "a1", verb: "act", name: "reserve" } },
    { action: { id: "a2", verb: "act", name: "charge" } },
  ],
  { actor: "checkout" },
);
console.log(result.completed.join(","), result.compensated.join(","), result.error);
