/** The person already dismissed this signal. */

import { DecisionClient } from "../../../../../packages/typescript/laix/src/index.ts";

const [decision] = new DecisionClient().decide({
  subject: "electricity bill",
  at: "2026-11-01T10:00:00Z",
  signals: [
    {
      id: "bill-1",
      kind: "deadline",
      title: "Electricity bill due tomorrow",
      severity: "high",
      confidence: 0.95,
    },
  ],
  context: {
    now: "2026-11-01T10:00:00Z",
    quietHours: null,
    feedback: { "bill-1": { state: "dismissed" } },
  },
})!;

console.log(decision.verb, decision.reasonCode);
