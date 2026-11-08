/** Record what a decision changed, not a click. */
import { OutcomeLedger } from "../../../../../packages/typescript/laix/src/index.ts";

const ledger = new OutcomeLedger();
ledger.add({
  id: "o-1",
  decisionId: "d-1",
  metric: "time_to_assessment",
  before: 10,
  after: 8,
  delta: -2,
  label: "helped",
  attributed: true,
  direction: "lower-better",
});
console.log(ledger.forDecision("d-1")[0].label, ledger.all()[0].delta, ledger.summary().helped);
