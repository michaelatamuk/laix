/** Turn open commitments into the next task move. */

import {
  CommitmentLedger,
  PlanningPolicy,
} from "../../../packages/typescript/laix/src/index.ts";

const ledger = new CommitmentLedger([
  { id: "a", subject: "send the draft", due: "2026-11-01T09:00:00Z" },
]);
const [decision] = new PlanningPolicy(ledger).decide({
  subject: "the task",
  at: "2026-11-01T10:00:00Z",
});

console.log(decision.verb, decision.reasonCode, decision.actionId);
