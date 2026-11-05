/** LAIX decides, the host executes, the receipt records what happened. */
import { DecisionRuntime, ExecutionBridge } from "../../../packages/typescript/laix/src/index.ts";

const runtime = new DecisionRuntime({
  bridge: new ExecutionBridge({ handlers: { "close the valve": (action) => ({ done: action.name }) } }),
});
const decision = runtime.decide(
  {
    id: "sink-1",
    at: "2026-11-01T10:00:00Z",
    subject: "kitchen sink",
    beliefs: [{ confidence: 0.95 }],
    attributes: { urgency: 0.9 },
  },
  [
    { id: "option-wait", verb: "wait", name: "keep watching", expectedBenefit: 0.1 },
    { id: "option-close-valve", verb: "act", name: "close the valve", expectedBenefit: 0.95, risk: 0.05, reversible: true },
  ],
);
const receipt = runtime.execute(decision, { actor: "agent" });
console.log(receipt.status, receipt.actionName);
