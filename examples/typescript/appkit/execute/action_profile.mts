import {
  ExecutionBridge,
} from "../../../../packages/typescript/laix/src/index.ts";
import type {
  ActionOption,
  Decision,
} from "../../../../packages/typescript/laix/src/index.ts";

const profileRequest = {
  decisionId: "DEC-1",
  traceId: "TRC-1",
  actor: "incident-bot",
  approver: "alice",
  context: { caseId: "C-1042" },
};

const decision: Decision = {
  verb: "act",
  confidence: 0.9,
  reasonCode: "safe_action",
  rationale: "the action is approved",
  decisionId: profileRequest.decisionId,
  traceId: profileRequest.traceId,
  actionId: "close",
  requiresApproval: true,
};
const action: ActionOption = { id: "close", verb: "act", name: "close case" };

const bridge = new ExecutionBridge({
  handlers: {
    "close case": (_action, context) => ({ closed: context.caseId }),
  },
});
const receipt = bridge.execute(decision, {
  action,
  actor: profileRequest.actor,
  approver: profileRequest.approver,
  context: profileRequest.context,
});

console.log(receipt.status, receipt.actionName);
