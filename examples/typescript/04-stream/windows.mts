import {
  ManualClock,
  StreamSession,
} from "../../../packages/typescript/laix/src/index.ts";
import type {
  Decision,
  DecisionRequest,
} from "../../../packages/typescript/laix/src/index.ts";

function decider(request: DecisionRequest): Decision[] {
  return [
    {
      verb: "guide",
      confidence: 0.9,
      reasonCode: "window_ready",
      rationale: request.subject,
      decisionId: `DEC-${request.subject}`,
    },
  ];
}

async function* events(): AsyncIterable<DecisionRequest> {
  yield { subject: "a", at: "2026-11-01T10:00:00.100Z" };
  yield { subject: "b", at: "2026-11-01T10:00:00.900Z" };
  yield { subject: "c", at: "2026-11-01T10:00:01.100Z" };
}

const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
const session = new StreamSession(decider, { clock: () => clock.now });
const decisions: string[] = [];
for await (const decision of session.feedWindows(events(), {
  windowMs: 1000,
  onWindow: (batch) => ({
    subject: `${batch.events.length} events`,
    at: batch.end.toISOString(),
  }),
})) {
  decisions.push(decision.rationale);
}
console.log(decisions);
