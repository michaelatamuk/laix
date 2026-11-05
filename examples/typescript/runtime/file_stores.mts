import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  CommitmentLedger,
  FileCommitmentStore,
  FileStreamCheckpointStore,
  StreamSession,
} from "../../../packages/typescript/laix/src/index.ts";
import type {
  CheckpointFiles,
  Commitment,
  CommitmentFiles,
  Decision,
  DecisionRequest,
} from "../../../packages/typescript/laix/src/index.ts";

function decider(request: DecisionRequest): Decision[] {
  return [
    {
      verb: "guide",
      confidence: 0.9,
      reasonCode: "worth_surfacing",
      rationale: request.subject,
      decisionId: `DEC-${request.subject}`,
    },
  ];
}

const checkpointFiles: CheckpointFiles = {
  join: (directory, name) => join(directory, name),
  read: (path) => (existsSync(path) ? readFileSync(path, "utf8") : null),
  write: (path, text) => writeFileSync(path, text, "utf8"),
  remove: (path) => {
    if (existsSync(path)) unlinkSync(path);
  },
};
const commitmentFiles: CommitmentFiles = checkpointFiles;

const directory = join(tmpdir(), `laix-file-stores-${Date.now()}`);
mkdirSync(directory, { recursive: true });
try {
  const checkpoints = new FileStreamCheckpointStore(directory, checkpointFiles);
  const session = new StreamSession(decider, { streamId: "stream-a" });
  session.observe({ subject: "case", at: "2026-11-01T10:00:00Z" });
  session.save(checkpoints, "case-1");

  const restored = new StreamSession(decider, { streamId: "stream-a" });
  restored.resume(checkpoints, "case-1");

  const commitments = new FileCommitmentStore(directory, commitmentFiles);
  const ledger = new CommitmentLedger([
    { id: "a", subject: "send the draft", due: "2026-11-01T09:00:00Z" } as Commitment,
  ]);
  commitments.save("task-1", ledger);
  console.log(restored.pending, commitments.load("task-1")!.get("a").subject);
} finally {
  rmSync(directory, { recursive: true, force: true });
}
