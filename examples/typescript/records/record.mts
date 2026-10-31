/** Record a decision, approve it, execute it, then verify the fingerprint. */

import {
  approveRecord,
  createDecisionRecord,
  evidenceFromQuotes,
  markExecuted,
  verifyRecord,
} from "../../../typescript/laix/src/index.ts";

const record = createDecisionRecord(
  {
    title: "Pay the electricity bill",
    decision: "Pay 42.00 today.",
    evidence: evidenceFromQuotes([
      { id: "bill-1", kind: "quote", quote: "The bill is due today." },
    ]),
  },
  { now: "2026-11-01T10:00:00Z", id: "rec-1" },
);
const approved = approveRecord(record, { by: "owner", at: "2026-11-01T10:05:00Z" });
const executed = markExecuted(approved, { by: "owner", at: "2026-11-01T10:06:00Z" });

console.log(executed.status, verifyRecord(executed));
