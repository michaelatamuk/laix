/** A quality reading chooses a guide action instead of immediate action. */

import { DecisionClient } from "../../../packages/typescript/laix/src/index.ts";

const [decision] = new DecisionClient().decide({
  subject: "quality reading",
  at: "2026-11-01T10:00:00Z",
  situation: {
    id: "reading-1",
    at: "2026-11-01T10:00:00Z",
    subject: "line-6 hydrogen reading",
    beliefs: [{ confidence: 0.8 }],
    attributes: { urgency: 0.6 },
  },
  options: [
    { id: "wait", verb: "wait", name: "keep observing", expectedBenefit: 0.2 },
    { id: "open-watch", verb: "guide", name: "open a watch", expectedBenefit: 0.6 },
    { id: "notify-engineer", verb: "act", name: "notify the engineer", expectedBenefit: 0.9 },
  ],
})!;

console.log(decision.verb, decision.reasonCode, decision.actionId);
