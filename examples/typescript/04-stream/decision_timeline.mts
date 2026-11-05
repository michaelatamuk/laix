import {
  DecisionTimeline,
} from "../../../packages/typescript/laix/src/index.ts";
import type { Decision } from "../../../packages/typescript/laix/src/index.ts";

const timeline = new DecisionTimeline();
timeline.add({
  verb: "guide",
  confidence: 0.8,
  reasonCode: "stream",
  rationale: "a first decision",
  decisionId: "d1",
  streamId: "desk",
  eventTime: "2026-11-01T10:00:00Z",
} as Decision);
timeline.add({
  verb: "act",
  confidence: 0.9,
  reasonCode: "stream",
  rationale: "a revision",
  decisionId: "d2",
  streamId: "desk",
  eventTime: "2026-11-01T10:01:00Z",
  revision: 1,
  supersedes: "d1",
} as Decision);

const report = timeline.report();
const latest = timeline.latest();
const history = timeline.history("d2").map((item) => item.decisionId).join(",");
console.log(report.decisions, report.chains, latest?.decisionId, history);
