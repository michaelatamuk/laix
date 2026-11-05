/** Read NDJSON lines into decision requests. */

import { fromNdjson } from "../../../packages/typescript/laix/src/index.ts";

async function* lines(): AsyncIterable<string> {
  yield '{"subject":"a","at":"2026-11-01T10:00:00Z"}\n';
  yield '{"subject":"b","at":"2026-11-01T10:00:01Z"}\n';
}

const subjects: string[] = [];
for await (const item of fromNdjson(lines())) subjects.push(item.subject);
console.log(subjects.join(" "));
