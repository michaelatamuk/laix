import { decisionAttributes } from "../../../../packages/typescript/laix/src/index.ts";
import type { Decision } from "../../../../packages/typescript/laix/src/index.ts";

const decision: Decision = {
  verb: "act",
  confidence: 0.92,
  reasonCode: "safe_action",
  rationale: "the valve is inside the risk limit",
  decisionId: "DEC-1",
  traceId: "TRC-1",
  policyVersion: "live.v1",
  actionId: "valve",
  requiresApproval: true,
};

const attributes = decisionAttributes(decision);
console.log(
  attributes["laix.verb"],
  attributes["laix.reason_code"],
  attributes["laix.action.id"],
  attributes["laix.approval.required"],
);
