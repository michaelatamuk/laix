import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DecisionTimeline } from "../src/index.ts";
import type { Decision } from "../src/index.ts";

function decision(
  decisionId: string,
  options: {
    revision?: number;
    supersedes?: string | null;
    streamId?: string;
    eventTime?: string;
  } = {},
): Decision {
  return {
    verb: "guide",
    confidence: 0.8,
    reasonCode: "stream",
    rationale: "a stream decision",
    decisionId,
    streamId: options.streamId ?? "desk",
    eventTime: options.eventTime ?? "2026-11-01T10:00:00Z",
    revision: options.revision ?? 0,
    supersedes: options.supersedes ?? null,
  };
}

describe("decision timeline", () => {
  it("forms a chain from a root to its revision", () => {
    const timeline = new DecisionTimeline();
    const root = timeline.add(decision("d1"));
    const revised = timeline.add(
      decision("d2", {
        revision: 1,
        supersedes: "d1",
        eventTime: "2026-11-01T10:01:00Z",
      }),
    );

    assert.deepEqual(timeline.history("d2"), [root, revised]);
    assert.deepEqual(timeline.current(), [revised]);
    assert.equal(timeline.isSuperseded("d1"), true);
    assert.equal(timeline.isSuperseded("d2"), false);
    const report = timeline.report();
    assert.equal(report.valid, true);
    assert.equal(report.decisions, 2);
    assert.equal(report.chains, 1);
    assert.equal(report.superseded, 1);
  });

  it("rejects invalid revisions", () => {
    assert.throws(() => new DecisionTimeline([decision("d1"), decision("d1")]));
    assert.throws(() =>
      new DecisionTimeline().add(decision("d1", { supersedes: "d0" })),
    );
    assert.throws(() =>
      new DecisionTimeline().add(decision("d2", { revision: 1, supersedes: "d1" })),
    );
    assert.throws(() => {
      const timeline = new DecisionTimeline([decision("d1")]);
      timeline.add(decision("d2", { revision: 2, supersedes: "d1" }));
    });
  });

  it("rejects a stream mismatch and backwards event time", () => {
    assert.throws(() => {
      const timeline = new DecisionTimeline([decision("d1", { streamId: "desk" })]);
      timeline.add(decision("d2", { revision: 1, supersedes: "d1", streamId: "phone" }));
    });
    assert.throws(() => {
      const timeline = new DecisionTimeline([decision("d1")]);
      timeline.add(
        decision("d2", {
          revision: 1,
          supersedes: "d1",
          eventTime: "2026-11-01T09:59:00Z",
        }),
      );
    });
  });

  it("reports late events", () => {
    const timeline = new DecisionTimeline([
      decision("d1", { eventTime: "2026-11-01T10:00:00Z" }),
      decision("d2", { eventTime: "2026-11-01T10:05:00Z" }),
    ]);

    assert.deepEqual(timeline.late("2026-11-01T10:03:00Z"), [timeline.get("d1")]);
  });

  it("round-trips the timeline", () => {
    const timeline = new DecisionTimeline([
      decision("d1"),
      decision("d2", { revision: 1, supersedes: "d1" }),
    ]);
    const restored = DecisionTimeline.fromDict(timeline.toDict());

    assert.deepEqual(restored.report(), timeline.report());
    assert.deepEqual(restored.history("d2"), timeline.history("d2"));
  });

  it("accepts a valid timeline", () => {
    assert.doesNotThrow(() => new DecisionTimeline().assertValid());
  });
});
