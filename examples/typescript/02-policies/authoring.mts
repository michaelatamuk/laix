import {
  RulePolicy,
  TargetedPolicy,
} from "../../../packages/typescript/laix/src/index.ts";

const policy = new TargetedPolicy(
  new RulePolicy([
    { when: { amount: { gte: 500 } }, verb: "ask", reasonCode: "over_limit" },
    { when: { priority: "high" }, verb: "act", reasonCode: "priority" },
  ]),
  { target: "some", recipients: ["alice", "ben"] },
);
const decision = policy.decide({
  subject: "refund",
  at: "2026-11-01T10:00:00Z",
  attributes: { amount: 780 },
})[0]!;
console.log(
  decision.verb,
  decision.reasonCode,
  decision.target,
  decision.recipients?.join(","),
);
