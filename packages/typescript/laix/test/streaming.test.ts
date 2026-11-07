import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ManualClock, StreamSession, TumblingWindow, fromSync, prometheus, runStreamBench } from "../src/index.ts";
import type { Decision, DecisionRequest } from "../src/index.ts";
import { DecisionClient } from "../src/index.ts";

const at = (second: number): string =>
  `2026-11-01T10:00:${String(second).padStart(2, "0")}+00:00`;

const request = (subject: string, second: number): DecisionRequest => ({
  subject,
  at: at(second),
});

function decider(input: DecisionRequest): Decision[] {
  return [
    {
      verb: "guide",
      confidence: 0.9,
      reasonCode: "worth_surfacing",
      rationale: input.subject,
      decisionId: `DEC-${input.subject}`,
    },
  ];
}

async function collect(session: StreamSession): Promise<Decision[]> {
  const out: Decision[] = [];
  for await (const decision of session.decisions()) out.push(decision);
  return out;
}

describe("stream session", () => {
  it("stamps the stream fields", () => {
    const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
    const session = new StreamSession(decider, {
      streamId: "STR-1",
      capacity: 4,
      clock: () => clock.now,
    });
    const out = session.observe({
      subject: "a",
      at: at(0),
      deadline: at(5),
      validUntil: at(9),
    });

    assert.equal(out.length, 1);
    assert.equal(out[0]!.streamId, "STR-1");
    assert.equal(out[0]!.eventTime, at(0));
    assert.equal(out[0]!.deadline, at(5));
    assert.equal(out[0]!.validUntil, at(9));
    assert.equal(out[0]!.status, "final");
    assert.equal(session.pending, 1);
  });

  it("drains decisions and closes", async () => {
    const session = new StreamSession(decider, { capacity: 4 });
    session.observe(request("a", 0));
    session.observe(request("b", 1));
    session.close();

    const decisions = await collect(session);
    assert.deepEqual(
      decisions.map((item) => item.rationale),
      ["a", "b"],
    );
  });

  it("drops a late event", () => {
    const session = new StreamSession(decider, { late: "drop" });
    assert.equal(session.observe(request("new", 5)).length, 1);
    assert.equal(session.observe(request("late", 1)).length, 0);
    assert.equal(session.stats.late, 1);
  });

  it("throttles inside the cooldown", () => {
    const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
    const session = new StreamSession(decider, {
      cooldownMs: 1000,
      clock: () => clock.now,
    });

    assert.equal(session.observe(request("a", 0)).length, 1);
    clock.set(new Date("2026-11-01T10:00:00.500Z"));
    assert.equal(session.observe(request("b", 0)).length, 0);
    assert.equal(session.stats.throttled, 1);

    clock.set(new Date("2026-11-01T10:00:01.100Z"));
    assert.equal(session.observe(request("c", 1)).length, 1);
  });

  it("keeps only the latest decision with latest_wins", async () => {
    const session = new StreamSession(decider, { capacity: 2, onFull: "latest_wins" });
    for (let index = 0; index < 5; index += 1) session.observe(request(String(index), index));

    assert.equal(session.pending, 1);
    assert.equal(session.stats.dropped, 4);
    session.close();
    const decisions = await collect(session);
    assert.deepEqual(
      decisions.map((item) => item.rationale),
      ["4"],
    );
  });

  it("marks a revision", () => {
    const session = new StreamSession(decider);
    const first = session.observe(request("a", 0))[0]!;
    const revised = session.revise(first, request("a", 1));

    assert.equal(revised[0]!.revision, 1);
    assert.equal(revised[0]!.supersedes, first.decisionId);
    assert.equal(session.stats.revised, 1);
  });

  it("stamps a missing decision id", () => {
    const bare = (input: DecisionRequest): Decision[] => [
      {
        verb: "guide",
        confidence: 0.9,
        reasonCode: "bare",
        rationale: input.subject,
      },
    ];
    const session = new StreamSession(bare);
    const out = session.observe(request("a", 0));

    assert.ok(out[0]!.decisionId);
  });

  it("marks a missed deadline as provisional", () => {
    const clock = new ManualClock(new Date("2026-11-01T10:00:05Z"));
    const session = new StreamSession(decider, { clock: () => clock.now });
    const out = session.observe({ subject: "a", at: at(0), deadline: at(1) });

    assert.equal(out[0]!.status, "provisional");
    assert.equal(session.stats.expired, 1);
    assert.equal(session.stats.provisional, 1);
  });

  it("suppresses the same batch inside hysteresis", () => {
    const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
    const session = new StreamSession(decider, { clock: () => clock.now, hysteresisMs: 1000 });

    assert.equal(session.observe(request("a", 0)).length, 1);
    clock.set(new Date("2026-11-01T10:00:00.500Z"));
    assert.equal(session.observe(request("b", 0)).length, 0);
    assert.equal(session.stats.suppressed, 1);
  });

  it("sheds after the per-window budget", () => {
    const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
    const session = new StreamSession(decider, {
      clock: () => clock.now,
      maxDecisionsPerWindow: 1,
      budgetWindowMs: 1000,
    });

    assert.equal(session.observe(request("a", 0)).length, 1);
    clock.set(new Date("2026-11-01T10:00:00.500Z"));
    assert.equal(session.observe(request("b", 0)).length, 0);
    assert.equal(session.stats.shed, 1);
  });

  it("records decision latency", () => {
    const slow = (input: DecisionRequest): Decision[] => {
      const started = Date.now();
      while (Date.now() - started < 5) {
        // spin for a measurable delay
      }
      return decider(input);
    };
    const session = new StreamSession(slow);
    session.observe(request("a", 0));

    assert.ok(session.stats.latencyP50 > 0);
    assert.ok(session.stats.latencyP95 >= session.stats.latencyP50);
  });

  it("refines a provisional decision", async () => {
    const session = new StreamSession(decider);
    const decisions = await session.observeRefined(request("a", 0), async () => [
      {
        verb: "act",
        confidence: 0.99,
        reasonCode: "deep_path",
        rationale: "deep",
        decisionId: "DEC-deep",
      },
    ]);

    assert.equal(decisions[0]!.status, "provisional");
    assert.equal(decisions[1]!.status, "final");
    assert.equal(decisions[1]!.revision, 1);
    assert.equal(decisions[1]!.supersedes, decisions[0]!.decisionId);
  });

  it("coalesces a busy feed", async () => {
    async function* events(): AsyncIterable<DecisionRequest> {
      yield request("a", 0);
      await new Promise((resolve) => setTimeout(resolve, 1));
      yield request("b", 1);
      await new Promise((resolve) => setTimeout(resolve, 50));
      yield request("c", 2);
      await new Promise((resolve) => setTimeout(resolve, 50));
    }

    const session = new StreamSession(decider);
    const out: Decision[] = [];
    for await (const decision of session.feed(events(), { coalesceMs: 20 })) out.push(decision);

    assert.equal(session.pending, 0);
    assert.deepEqual(
      out.map((item) => item.rationale),
      ["b", "c"],
    );
  });

  it("closes tumbling windows", () => {
    const window = new TumblingWindow(10_000);
    assert.equal(window.add(request("a", 0)).length, 0);
    assert.equal(window.add(request("b", 5)).length, 0);
    const batches = window.add(request("c", 11));

    assert.equal(batches.length, 1);
    assert.equal(batches[0]!.events.length, 2);
    assert.equal(window.flush()[0]!.events.length, 1);
  });

  it("aggregates windows into decisions", async () => {
    async function* events(): AsyncIterable<DecisionRequest> {
      for (const second of [0, 1, 11, 12]) yield request(`e${second}`, second);
    }

    const session = new StreamSession(decider);
    const out: Decision[] = [];
    for await (const decision of session.feedWindows(events(), {
      windowMs: 10_000,
      onWindow: (batch) => ({ subject: `n${batch.events.length}`, at: batch.end.toISOString() }),
    })) {
      out.push(decision);
    }

    assert.deepEqual(
      out.map((item) => item.rationale),
      ["n2", "n2"],
    );
  });

  it("replays without filling the buffer", () => {
    const session = new StreamSession(decider);
    const decisions = session.replay([request("a", 0), request("b", 1), request("c", 2)]);

    assert.deepEqual(
      decisions.map((item) => item.rationale),
      ["a", "b", "c"],
    );
    assert.equal(session.pending, 0);
    assert.equal(session.stats.observed, 3);
  });

  it("restores a snapshot", () => {
    const session = new StreamSession(decider);
    const decision = session.observe(request("a", 5))[0]!;
    const snapshot = session.snapshot();

    const restored = new StreamSession(decider);
    restored.restore(snapshot);

    assert.equal(restored.stats.decided, 1);
    assert.equal(restored.trace(decision.decisionId!).events[0]!.stage, "decided");
    assert.equal(restored.observe(request("late", 1)).length, 0);
    assert.equal(restored.stats.late, 1);
  });

  it("restores pending decisions", async () => {
    const session = new StreamSession(decider);
    session.observe(request("a", 0));
    session.observe(request("b", 1));
    const restored = new StreamSession(decider);
    restored.restore(session.snapshot());
    restored.close();

    const decisions = await collect(restored);
    assert.deepEqual(
      decisions.map((item) => item.rationale),
      ["a", "b"],
    );
  });

  it("drops a duplicate event", () => {
    const clock = new ManualClock(new Date("2026-11-01T10:00:00Z"));
    const session = new StreamSession(decider, { clock: () => clock.now, dedupeMs: 1000 });

    assert.equal(
      session.observe({ subject: "a", at: at(0), eventId: "e1" }).length,
      1,
    );
    assert.equal(
      session.observe({ subject: "b", at: at(0), eventId: "e1" }).length,
      0,
    );
    assert.equal(session.stats.duplicates, 1);

    clock.set(new Date("2026-11-01T10:00:02Z"));
    assert.equal(
      session.observe({ subject: "c", at: at(2), eventId: "e1" }).length,
      1,
    );
  });

  it("keeps a trace and calls the recorder", () => {
    const recorded: Decision[] = [];
    const session = new StreamSession(decider, { recorder: (item) => recorded.push(item) });
    const decision = session.observe(request("a", 0))[0]!;

    assert.ok(decision.traceId);
    assert.equal(session.trace(decision.decisionId!).events[0]!.stage, "decided");
    assert.deepEqual(recorded, [decision]);
  });

  it("times out the deep path and finalizes the provisional", async () => {
    const session = new StreamSession(decider);
    const decisions = await session.observeRefined(
      request("a", 0),
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 50));
        return [
          {
            verb: "act",
            confidence: 0.99,
            reasonCode: "deep_path",
            rationale: "deep",
            decisionId: "DEC-deep",
          },
        ];
      },
      { timeoutMs: 5 },
    );

    assert.equal(session.stats.refineTimeouts, 1);
    assert.equal(decisions[0]!.status, "provisional");
    assert.equal(decisions[1]!.status, "final");
    assert.equal(decisions[1]!.supersedes, decisions[0]!.decisionId);
  });

  it("waits for buffer space", async () => {
    const session = new StreamSession(decider, { capacity: 1 });
    session.observe(request("a", 0));
    const waiting = session.observeWait(request("b", 1));
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(session.pending, 1);

    const iterator = session.decisions();
    const first = await iterator.next();
    await waiting;
    const second = await iterator.next();

    assert.equal(first.value!.rationale, "a");
    assert.equal(second.value!.rationale, "b");
  });

  it("is available from the DecisionClient", () => {
    const layer = new DecisionClient();
    const session = layer.stream({ streamId: "STR-L" });
    const out = session.observe({
      subject: "a",
      at: at(0),
      signals: [{ id: "s-1", kind: "k", severity: "high", confidence: 0.9 }],
      context: { now: at(0), quietHours: null },
    });

    assert.equal(out.length, 1);
    assert.equal(out[0]!.streamId, "STR-L");
  });

  it("exports counters and benches a stream", async () => {
    async function* events(): AsyncIterable<DecisionRequest> {
      yield request("a", 0);
      yield request("b", 1);
    }

    const session = new StreamSession(decider);
    const out: Decision[] = [];
    for await (const decision of session.feed(fromSync(await collectAsync(events())))) out.push(decision);
    assert.equal(prometheus(session.stats).includes("laix_stream_decided 2"), true);
    assert.equal(runStreamBench(session, [request("c", 2)]).decisions.length, 1);
  });
});

async function collectAsync(events: AsyncIterable<DecisionRequest>): Promise<DecisionRequest[]> {
  const out: DecisionRequest[] = [];
  for await (const event of events) out.push(event);
  return out;
}
