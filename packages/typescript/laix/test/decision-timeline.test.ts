import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  AttentionBudget,
  DecisionTimeline,
  ManualClock,
  StreamSession,
} from "../src/index.ts";
import type { Decision, DecisionRequest } from "../src/index.ts";

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

  it("spends a shared attention budget in a stream", () => {
    const decider = (request: DecisionRequest): Decision[] => [
      {
        verb: "guide",
        confidence: 0.8,
        reasonCode: "stream",
        rationale: "a stream decision",
        decisionId: `DEC-${request.at}`,
        attributes: { attention_cost: 0.4 },
      },
    ];
    const budget = new AttentionBudget({ total: 1 });
    const session = new StreamSession(decider, {
      streamId: "STR-1",
      clock: () => new Date("2026-11-01T10:00:00Z"),
      attentionBudget: budget,
    });
    session.observe({ subject: "a", at: "2026-11-01T10:00:00Z" });
    session.observe({ subject: "b", at: "2026-11-01T10:00:01Z" });

    assert.equal(Math.round(budget.remaining() * 1e6) / 1e6, 0.2);
    const restored = new StreamSession(decider, { streamId: "STR-1" });
    restored.restore(session.snapshot());
    assert.equal(
      Math.round((restored.attentionBudget?.remaining() ?? 0) * 1e6) / 1e6,
      0.2,
    );
  });

  it("accepts a valid timeline", () => {
    assert.doesNotThrow(() => new DecisionTimeline().assertValid());
  });

  it("is fed by a stream session", () => {
    const timeline = new DecisionTimeline();
    const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
    const decider = (request: DecisionRequest): Decision[] => [
      {
        verb: "guide",
        confidence: 0.8,
        reasonCode: "stream",
        rationale: "a stream decision",
        decisionId: `DEC-${request.at}`,
      },
    ];
    const session = new StreamSession(decider, {
      streamId: "STR-1",
      clock: () => clock.now,
      timeline,
    });
    const first = session.observe({
      subject: "a",
      at: "2026-11-01T10:00:00Z",
    })[0]!;
    const second = session.revise(first, {
      subject: "a",
      at: "2026-11-01T10:00:01Z",
    })[0]!;

    assert.equal(timeline.report().decisions, 2);
    assert.deepEqual(timeline.history(second.decisionId!), [first, second]);
  });
});
