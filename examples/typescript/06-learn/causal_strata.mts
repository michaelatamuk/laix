import { CausalLedger } from "../../../packages/typescript/laix/src/index.ts";

const ledger = new CausalLedger();
for (const [decisionId, arm, outcome, stratum] of [
  ["e1", "ask", 1, "east"],
  ["e2", "ask", 3, "east"],
  ["e3", "wait", 0, "east"],
  ["e4", "wait", 2, "east"],
  ["w1", "ask", 2, "west"],
  ["w2", "wait", 1, "west"],
] as Array<[string, string, number, string]>) {
  ledger.add(decisionId, { arm, outcome, context: { stratum } });
}

const overall = ledger.effect("ask", "wait");
const east = ledger.effectByContext("ask", "wait").east!;
console.log(
  overall.estimate,
  east.ciLow,
  east.ciHigh,
  Object.keys(ledger.effectByContext("ask", "wait")).sort(),
);
