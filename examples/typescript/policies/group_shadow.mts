import {
  GroupPolicy,
  RulePolicy,
  ShadowPolicy,
} from "../../../packages/typescript/laix/src/index.ts";

const primary = new RulePolicy([
  { when: { amount: { gte: 500 } }, verb: "ask", reasonCode: "over_limit" },
]);
const shadow = new RulePolicy([
  { when: { amount: { gte: 500 } }, verb: "act", reasonCode: "over_limit" },
]);
const comparison = new ShadowPolicy(primary, shadow);
const decision = comparison.decide({
  subject: "refund",
  at: "2026-11-01T10:00:00Z",
  attributes: { amount: 780 },
})[0]!;

const group = new GroupPolicy(
  {
    decide: () => [
      {
        verb: "guide",
        confidence: 0.9,
        reasonCode: "share",
        rationale: "share",
        attributes: { topic: "math", health: "private" },
      },
    ],
  },
  {
    target: "all",
    recipients: ["alice", "ben", "chris"],
    privateAttributes: ["health"],
  },
);
const shared = group.decide({
  subject: "a task",
  at: "2026-11-01T10:00:00Z",
})[0]!;

console.log(
  decision.verb,
  comparison.differences[0]!.shadow[0]!.verb,
  shared.target,
  JSON.stringify(shared.attributes),
);
