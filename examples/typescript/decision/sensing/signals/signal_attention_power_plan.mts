import {
  DecisionClient,
  type DecisionRequest,
} from "../../../../../packages/typescript/laix/src/index.ts";

const request: DecisionRequest = {
  subject: "power plan review",
  at: "2026-11-01T10:00:00Z",
  signals: [
    {
      id: "risk-1",
      kind: "power",
      title: "The power plan is below the required load",
      severity: "high",
      confidence: 0.9,
      due: "2026-11-03T09:00:00Z",
      evidenceRefs: ["power-study-4"],
    },
  ],
  context: {
    now: "2026-11-01T10:00:00Z",
    quietHours: ["22:00", "06:00"],
    minSeverity: "medium",
  },
};
const decision = new DecisionClient().decide(request)[0]!;

console.log(decision.verb, decision.reasonCode, decision.score);
