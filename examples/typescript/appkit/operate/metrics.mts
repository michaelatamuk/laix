/** Export stream counters in Prometheus text format. */

import {
  ManualClock,
  StreamSession,
  prometheus,
} from "../../../../packages/typescript/laix/src/index.ts";
import type {
  Decision,
  DecisionRequest,
} from "../../../../packages/typescript/laix/src/index.ts";

function decider(request: DecisionRequest): Decision[] {
  return [
    {
      verb: "guide",
      confidence: 0.9,
      reasonCode: "worth_surfacing",
      rationale: request.subject,
      decisionId: `DEC-${request.subject}`,
    },
  ];
}

const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
const session = new StreamSession(decider, { clock: () => clock.now });
session.observe({ subject: "a", at: "2026-11-01T10:00:00Z" });
const text = prometheus(session.stats);
console.log(session.stats.decided, text.includes("laix_stream_decided 1"));
