import {
  CausalLedger,
  CommitmentLedger,
  PlanningPolicy,
} from "../../../../../packages/typescript/laix/src/index.ts";

const causal = new CausalLedger();
causal.add("d1", { arm: "ask", outcome: 1 });
causal.add("d2", { arm: "ask", outcome: 1 });
causal.add("d3", { arm: "wait", outcome: 0 });
causal.add("d4", { arm: "wait", outcome: 0 });
const effect = causal.effect("ask", "wait");

const ledger = new CommitmentLedger([
  { id: "a", subject: "send the draft", due: "2026-11-01T09:00:00Z" },
]);
const decision = new PlanningPolicy(ledger).decide({
  subject: "the task",
  at: "2026-11-01T10:00:00Z",
})[0]!;

console.log(effect.estimate, effect.method, decision.verb, decision.actionId);
