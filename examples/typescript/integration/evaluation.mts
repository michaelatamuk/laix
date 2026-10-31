/** Compare a policy against expected decisions, case by case. */
import { compare } from "../../../packages/typescript/laix/src/index.ts";

const report = compare(
  [
    { id: "case-1", request: {}, expected: [{ verb: "wait", reasonCode: "policy_rule" }] },
    { id: "case-2", request: {}, expected: [{ verb: "wait", reasonCode: "policy_rule" }] },
  ],
  () => [{ verb: "wait", reasonCode: "policy_rule" }],
);
console.log(report.total, report.passed, report.agreementRate);
