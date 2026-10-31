/** A bill is due tomorrow. Ask the TypeScript Layer whether to show it now. */

import { Layer } from "../../../typescript/laix/src/index.ts";

const layer = new Layer();
const [decision] = layer.decide({
  subject: "electricity bill",
  at: "2026-11-01T10:00:00Z",
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
  context: { now: "2026-11-01T10:00:00Z", quietHours: ["22:00", "06:00"] },
});

console.log(decision.verb, decision.reasonCode, decision.score);
