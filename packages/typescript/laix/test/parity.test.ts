import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  BanditPolicy,
  CallableDetector,
  DecisionRuntime,
  ExecutionBridge,
  ExperienceState,
  InMemoryPlatform,
  InMemoryStateStore,
  Layer,
  LiveContext,
  NullDelivery,
  SafetyConstrainedPolicy,
  UCBBandit,
  applyProposal,
  approveProposal,
  compare,
  createProposal,
  runBench,
  undoProposal,
} from "../src/index.ts";
import type { PerceptionEvent } from "../src/index.ts";

describe("typescript parity", () => {
  it("runs the bench across every decision class", () => {
    const report = runBench();
    assert.equal(report.total, 25);
    assert.equal(report.passed, 25);
    assert.equal(report.agreement, 1);
    assert.equal(Object.keys(report.bySuite()).length, 10);
  });

  it("learns from rewards in a bandit policy", () => {
    const policy = new BanditPolicy(new UCBBandit([{ id: "manual" }, { id: "automatic" }]));
    const layer = new Layer({ policy });
    const request = { subject: "pick a mode", at: "2026-11-01T10:00:00Z" };
    assert.equal(layer.decide(request)[0].actionId, "manual");
    policy.record("manual", 0);
    policy.record("automatic", 1);
    assert.equal(layer.decide(request)[0].actionId, "automatic");
  });

  it("runs the in-memory platform", () => {
    const platform = new InMemoryPlatform({ approver: () => ({ approved: true, by: "owner" }) });
    platform.register("lookup", (call) => call.args?.value);
    assert.equal(platform.runSkill({ capability: "lookup", args: { value: 7 }, traceId: "tr-1" }), 7);
    assert.deepEqual(platform.events("tr-1").map((event) => event.kind), ["skill.started", "skill.finished"]);
    assert.equal(platform.requestApproval({ decisionId: "d-1", action: "assign" }).approved, true);
    assert.equal(platform.capability("fast").level, "fast");
  });

  it("saves and loads experience state", () => {
    const store = new InMemoryStateStore();
    const state = new ExperienceState("one", "decide");
    store.save("key", state);
    assert.equal(store.load("key")?.phase, "decide");
    store.delete("key");
    assert.equal(store.load("key"), null);
  });

  it("runs live context with a sub-second budget", () => {
    const context = new LiveContext([
      new CallableDetector("motion", (event) => [{ id: `m-${event.at}`, detector: "motion", kind: "presence", subject: event.subject, at: event.at, confidence: 0.8 }], { informationGain: 0.2 }),
      new CallableDetector("read-label", (event) => [{ id: `r-${event.at}`, detector: "read-label", kind: "presence", subject: event.subject, at: event.at, confidence: 0.95 }], { tier: "deep", cost: 0.1, latencyMs: 200, informationGain: 0.9 }),
      new CallableDetector("transcribe", (event) => [{ id: `t-${event.at}`, detector: "transcribe", kind: "presence", subject: event.subject, at: event.at }], { tier: "deep", cost: 0.1, latencyMs: 900, informationGain: 0.9 }),
    ]);
    const event: PerceptionEvent = { subject: "kitchen", at: "2026-11-01T10:00:00Z" };
    const frame = context.perceive(event, 0.8);
    assert.deepEqual(frame.allowed, ["motion", "read-label"]);
    assert.equal(frame.skipped[0].name, "transcribe");
    assert.equal(frame.detections.length, 2);
  });

  it("executes and records a decision", () => {
    const bridge = new ExecutionBridge({ handlers: { close: () => ({ done: true }) } });
    const runtime = new DecisionRuntime({ bridge });
    const decision = runtime.decide(
      { id: "s-1", at: "2026-11-01T10:00:00Z", subject: "sink", beliefs: [{ confidence: 0.95 }], attributes: { urgency: 0.9 } },
      [{ id: "a-close", verb: "act", name: "close", expectedBenefit: 0.95 }],
    );
    const receipt = runtime.execute(decision, { actor: "agent" });
    assert.equal(receipt.status, "executed");
    assert.equal(runtime.trace(decision.decisionId).events.at(-1)?.stage, "execution.executed");
    assert.equal(runtime.measure(decision.decisionId, { metric: "time", before: 10, after: 8, direction: "lower-better" }).label, "helped");
  });

  it("moves a proposal through its lifecycle", () => {
    const proposal = createProposal({ id: "p-1", title: "change", summary: "do it" });
    const approved = approveProposal(proposal, "owner");
    const applied = applyProposal(approved);
    assert.equal(undoProposal(applied).status, "undone");
  });

  it("records a delivery receipt", () => {
    const receipt = new NullDelivery().deliver({ decisionId: "d-1" }, "hello", { channel: "email" });
    assert.equal(receipt.status, "skipped");
    assert.equal(receipt.channel, "email");
  });

  it("compares cases with the parity harness", () => {
    const report = compare(
      [{ id: "one", request: {}, expected: [{ verb: "wait", reasonCode: "policy_rule" }] }],
      () => [{ verb: "wait", reasonCode: "policy_rule" }],
    );
    assert.equal(report.passed, 1);
    assert.equal(report.agreementRate, 1);
  });

  it("carries host confidence and its source", () => {
    const layer = new Layer();
    const [decision] = layer.decide({
      subject: "one task",
      at: "2026-11-01T10:00:00Z",
      situation: {
        id: "task-1",
        at: "2026-11-01T10:00:00Z",
        subject: "one task",
        beliefs: [{ confidence: 0.9 }],
        attributes: { urgency: 0.9 },
      },
      options: [
        { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.1 },
        { id: "act", verb: "act", name: "act", expectedBenefit: 0.9 },
      ],
      confidence: 0.86,
      confidenceSource: "host-calibrated",
      calibrated: true,
    });
    assert.equal(decision.confidence, 0.86);
    assert.equal(decision.confidenceSource, "host-calibrated");
    assert.equal(decision.calibrated, true);
  });

  it("escalates when a safety boundary is breached and no safe action remains", () => {
    const layer = new Layer();
    const [decision] = layer.decide({
      subject: "water near electricity",
      at: "2026-11-01T10:00:00Z",
      situation: {
        id: "leak-1",
        at: "2026-11-01T10:00:00Z",
        subject: "water near electricity",
        beliefs: [{ confidence: 0.9 }],
        constraints: [{ kind: "risk", value: 0.2, hard: true }],
        attributes: { urgency: 0.9, safety_breached: true },
      },
      options: [
        { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.1 },
        { id: "breaker", verb: "act", name: "cross wet floor", expectedBenefit: 1.0, risk: 0.9 },
        { id: "manager", verb: "escalate", name: "call manager", expectedBenefit: 0.7 },
      ],
    });
    assert.equal(decision.verb, "escalate");
    assert.equal(decision.actionId, "manager");
  });

  it("uses a policy plugin through Layer", () => {
    const layer = new Layer({ policy: new SafetyConstrainedPolicy() });
    const [decision] = layer.decide({
      subject: "sink",
      at: "2026-11-01T10:00:00Z",
      attributes: { risk_limit: 0.2, options: [{ id: "valve", benefit: 0.9, risk: 0.1 }] },
    });
    assert.equal(decision.verb, "act");
    assert.equal(decision.actionId, "valve");
  });
});
