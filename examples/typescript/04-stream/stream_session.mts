/** Streaming decisions: one event becomes a decision in a stream session. */
import { DecisionClient } from "../../../packages/typescript/laix/src/index.ts";

const layer = new DecisionClient();
const stream = layer.stream({ streamId: "STR-DEMO", capacity: 4, cooldownMs: 500 });

stream.observe({
  subject: "a bill is due",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "bill", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: null },
});
stream.close();

for await (const decision of stream.decisions()) {
  console.log(decision.verb, decision.reasonCode, decision.streamId, decision.status);
}
