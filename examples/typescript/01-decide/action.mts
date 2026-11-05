/** The kitchen sink is about to overflow. Ask the TypeScript Layer what to do. */

import { Layer } from "../../../packages/typescript/laix/src/index.ts";

const layer = new Layer();
const [decision] = layer.decide({
  subject: "kitchen sink",
  at: "2026-11-01T10:00:00Z",
  situation: {
    id: "sink-1",
    at: "2026-11-01T10:00:00Z",
    subject: "kitchen sink",
    beliefs: [{ confidence: 0.95 }],
    attributes: { urgency: 0.9 },
  },
  options: [
    { id: "option-wait", verb: "wait", name: "keep watching", expectedBenefit: 0.1 },
    {
      id: "option-close-valve",
      verb: "act",
      name: "close the valve",
      expectedBenefit: 0.95,
      risk: 0.05,
      reversible: true,
    },
  ],
});

console.log(decision.verb, decision.reasonCode, decision.actionId);
