import {
  ManualClock,
  StreamSession,
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
const session = new StreamSession(decider, {
  clock: () => clock.now,
  cooldownMs: 1000,
  maxDecisionsPerWindow: 1,
  budgetWindowMs: 2000,
});

clock.set(new Date("2026-11-01T10:00:00Z"));
const first = session.observe({ subject: "a", at: "2026-11-01T10:00:00Z" });
clock.set(new Date("2026-11-01T10:00:00.200Z"));
const second = session.observe({ subject: "b", at: "2026-11-01T10:00:00.200Z" });
clock.set(new Date("2026-11-01T10:00:01.200Z"));
const third = session.observe({ subject: "c", at: "2026-11-01T10:00:01.200Z" });

const replay = new StreamSession(decider, {
  clock: () => clock.now,
}).replay([
  { subject: "d", at: "2026-11-01T10:00:10Z" },
  { subject: "e", at: "2026-11-01T10:00:11Z" },
]);
console.log(
  first.length,
  second.length,
  third.length,
  session.stats.throttled,
  session.stats.shed,
  replay.map((item) => item.rationale),
);
