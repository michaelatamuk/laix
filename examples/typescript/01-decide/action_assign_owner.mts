/** An urgent alert assigns an owner; the assignment needs approval. */

import { Layer } from "../../../packages/typescript/laix/src/index.ts";

const [decision] = new Layer().decide({
  subject: "monitored area alert",
  at: "2026-11-01T10:00:00Z",
  situation: {
    id: "alert-1",
    at: "2026-11-01T10:00:00Z",
    subject: "new construction in a monitored area",
    beliefs: [{ confidence: 0.92 }],
    attributes: { urgency: 0.9 },
  },
  options: [
    { id: "wait", verb: "wait", name: "keep watching", expectedBenefit: 0.2 },
    { id: "request-check", verb: "ask", name: "request a better view", expectedBenefit: 0.6 },
    {
      id: "assign-owner",
      verb: "act",
      name: "assign an owner",
      expectedBenefit: 0.9,
      requiresApproval: true,
    },
  ],
})!;

console.log(decision.verb, decision.reasonCode, decision.actionId, decision.requiresApproval);
