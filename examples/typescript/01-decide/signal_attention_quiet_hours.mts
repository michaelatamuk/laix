/** The same bill arrives at night. Quiet hours hold it for the digest. */

import { DecisionClient } from "../../../packages/typescript/laix/src/index.ts";

const [decision] = new DecisionClient().decide({
  subject: "electricity bill",
  at: "2026-11-01T23:30:00Z",
  signals: [
    {
      id: "bill-1",
      kind: "deadline",
      title: "Electricity bill due tomorrow",
      severity: "high",
      confidence: 0.95,
      due: "2026-11-02T09:00:00Z",
    },
  ],
  context: { now: "2026-11-01T23:30:00Z", quietHours: ["22:00", "06:00"] },
})!;

console.log(decision.verb, decision.reasonCode, decision.score, decision.record, decision.deliver);
