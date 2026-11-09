/** A payment is due today, and a person must approve it. */

import { DecisionClient } from "../../../../../../packages/typescript/laix/src/index.ts";

const [decision] = new DecisionClient().decide({
  subject: "electricity bill payment",
  at: "2026-11-01T10:00:00Z",
  situation: {
    id: "payment-1",
    at: "2026-11-01T10:00:00Z",
    subject: "electricity bill payment",
    beliefs: [{ confidence: 0.95 }],
    attributes: { urgency: 0.9 },
  },
  options: [
    { id: "option-wait", verb: "wait", name: "pay later", expectedBenefit: 0.1 },
    {
      id: "option-pay",
      verb: "act",
      name: "pay the bill",
      expectedBenefit: 0.9,
      requiresApproval: true,
    },
  ],
})!;

console.log(decision.verb, decision.reasonCode, decision.actionId, decision.requiresApproval);
