import {
  DeadLetterQueue,
  fromNdjson,
} from "../../../../packages/typescript/laix/src/index.ts";

const dead = new DeadLetterQueue();
async function* lines(): AsyncIterable<string> {
  yield '{"subject":"a","at":"2026-11-01T10:00:00Z"}\n';
  yield '{"subject":\n';
  yield '{"subject":"b","at":"2026-11-01T10:00:01Z"}\n';
}

const subjects: string[] = [];
for await (const item of fromNdjson(lines(), {
  onError: dead.errorHandler(),
  strict: false,
})) {
  subjects.push(item.subject);
}
console.log(subjects.join(" "), dead.length, /SyntaxError|JSON/.test(dead.all()[0]!.error));
