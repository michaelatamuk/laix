import assert from "node:assert/strict";
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
import { describe, it } from "node:test";
import {
  DeadLetterQueue,
  FileStreamCheckpointStore,
  InMemoryStreamCheckpointStore,
  StreamSession,
  fromNdjson,
  fromSse,
} from "../src/index.ts";
import type { CheckpointFiles, Decision, DecisionRequest } from "../src/index.ts";

const files: CheckpointFiles = {
  join: (directory, name) => join(directory, name),
  read: (path) => (existsSync(path) ? readFileSync(path, "utf8") : null),
  write: (path, text) => writeFileSync(path, text, "utf8"),
  remove: (path) => {
    if (existsSync(path)) unlinkSync(path);
  },
};

function request(subject: string, second: number): DecisionRequest {
  return {
    subject,
    at: `2026-11-01T10:00:${String(second).padStart(2, "0")}Z`,
  };
}

function decider(item: DecisionRequest): Decision[] {
  return [
    {
      verb: "guide",
      confidence: 0.9,
      reasonCode: "worth_surfacing",
      rationale: item.subject,
      decisionId: `DEC-${item.subject}`,
    },
  ];
}

async function* lines(...items: string[]): AsyncIterable<string> {
  for (const item of items) yield item;
}

describe("stream checkpoints", () => {
  it("round trips an in-memory snapshot", () => {
    const store = new InMemoryStreamCheckpointStore();
    const session = new StreamSession(decider);
    session.observe(request("a", 0));
    session.save(store, "case-1");

    const restored = new StreamSession(decider);
    assert.equal(restored.resume(store, "case-1"), true);
    assert.equal(restored.pending, 1);
    assert.equal(restored.stats.decided, 1);

    store.delete("case-1");
    assert.equal(store.load("case-1"), null);
  });

  it("round trips a file snapshot", () => {
    const directory = join(tmpdir(), `laix-checkpoint-${Date.now()}`);
    mkdirSync(directory, { recursive: true });
    try {
      const store = new FileStreamCheckpointStore(directory, files);
      const session = new StreamSession(decider);
      session.observe(request("a", 0));
      session.save(store, "case-1");

      const restored = new StreamSession(decider);
      assert.equal(restored.resume(store, "case-1"), true);
      assert.equal(restored.pending, 1);
      store.delete("case-1");
      assert.equal(store.load("case-1"), null);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  it("rejects a checkpoint from another explicit stream", () => {
    const store = new InMemoryStreamCheckpointStore();
    const session = new StreamSession(decider, { streamId: "stream-a" });
    session.observe(request("a", 0));
    session.save(store, "case-2");

    const restored = new StreamSession(decider, { streamId: "stream-b" });
    assert.throws(() => restored.resume(store, "case-2"), /stream-a/);
  });
});

describe("stream sources", () => {
  it("reads one request per NDJSON line", async () => {
    const requests: DecisionRequest[] = [];
    for await (const item of fromNdjson(
      lines(
        '{"subject":"a","at":"2026-11-01T10:00:00Z"}\n',
        '{"subject":"b","at":"2026-11-01T10:00:01Z"}\n',
      ),
    )) {
      requests.push(item);
    }
    assert.deepEqual(requests.map((item) => item.subject), ["a", "b"]);
  });

  it("reads SSE data frames", async () => {
    const requests: DecisionRequest[] = [];
    for await (const item of fromSse(
      lines(
        'data: {"subject":"a","at":"2026-11-01T10:00:00Z"}\n',
        "\n",
        'data: {"subject":"b","at":"2026-11-01T10:00:01Z"}\n',
        "\n",
      ),
    )) {
      requests.push(item);
    }
    assert.deepEqual(requests.map((item) => item.subject), ["a", "b"]);
  });

  it("retains malformed NDJSON frames", async () => {
    const dead = new DeadLetterQueue(1);
    const requests: DecisionRequest[] = [];
    for await (const item of fromNdjson(
      lines(
        '{"subject":\n',
        '{"subject":"a","at":"2026-11-01T10:00:00Z"}\n',
      ),
      { onError: dead.errorHandler(), strict: false },
    )) {
      requests.push(item);
    }

    assert.deepEqual(requests.map((item) => item.subject), ["a"]);
    assert.equal(dead.length, 1);
    assert.equal(dead.all()[0]!.raw, '{"subject":');
    assert.match(dead.all()[0]!.error, /SyntaxError|JSON/);
  });
});
