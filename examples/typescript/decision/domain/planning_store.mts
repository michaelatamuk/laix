import {
  CommitmentLedger,
  InMemoryCommitmentStore,
} from "../../../../packages/typescript/laix/src/index.ts";

const ledger = new CommitmentLedger([
  { id: "a", subject: "send the draft", due: "2026-11-01T09:00:00Z" },
]);
const store = new InMemoryCommitmentStore();
store.save("task-1", ledger);
const restored = store.load("task-1")!;
console.log(restored.get("a").subject);
