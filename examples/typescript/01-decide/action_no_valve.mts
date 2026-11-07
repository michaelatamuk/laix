/** Water and electricity, with no safe valve to close. */

import { DecisionClient } from "../../../packages/typescript/laix/src/index.ts";

const [decision] = new DecisionClient().decide({
  subject: "water near electricity",
  at: "2026-11-01T10:00:00Z",
  situation: {
    id: "leak-1",
    at: "2026-11-01T10:00:00Z",
    subject: "water near electricity",
    beliefs: [{ confidence: 0.9 }, { confidence: 0.9 }],
    constraints: [{ kind: "risk", value: 0.2, hard: true }],
    attributes: { urgency: 0.9, safety_breached: true },
  },
  options: [
    { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.1 },
    { id: "look", verb: "observe", name: "look from the doorway", expectedBenefit: 0.5 },
    { id: "guide", verb: "guide", name: "keep people out", expectedBenefit: 0.6 },
    { id: "ask", verb: "ask", name: "call the owner", expectedBenefit: 0.4 },
    {
      id: "breaker",
      verb: "act",
      name: "cross the wet floor to the breaker",
      expectedBenefit: 1,
      risk: 0.9,
    },
    { id: "manager", verb: "escalate", name: "call a qualified person", expectedBenefit: 0.7 },
  ],
})!;

console.log(decision.verb, decision.actionId, decision.score);
