import {
  InMemoryStreamCheckpointStore,
  StreamSession,
  fromNdjson,
} from "../../../../packages/typescript/laix/src/index.ts";
import type {
  Decision,
  DecisionRequest,
} from "../../../../packages/typescript/laix/src/index.ts";

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

const store = new InMemoryStreamCheckpointStore();
const session = new StreamSession(decider);
session.observe({ subject: "case", at: "2026-11-01T10:00:00Z" });
session.save(store, "case-1");
const restored = new StreamSession(decider);

async function* lines(): AsyncIterable<string> {
  yield '{"subject":"a","at":"2026-11-01T10:00:00Z"}\n';
  yield '{"subject":"b","at":"2026-11-01T10:00:01Z"}\n';
}

const subjects: string[] = [];
for await (const item of fromNdjson(lines())) subjects.push(item.subject);
console.log(restored.resume(store, "case-1"), restored.pending, subjects.join(" "));
