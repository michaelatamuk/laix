import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CAVODPlanner,
  CaseBasedPlanner,
  CommitmentBeliefPlanner,
  CommitmentGraph,
  CommitmentLedger,
  CommitmentPlanner,
  CommitmentResolutionPlanner,
  ConflictResolutionPlanner,
  LiveCompositePlanner,
  MdpModel,
  PortfolioPlanner,
  RevalidationPlanner,
  RiskBoundedPlanner,
  commitmentTrusted,
  commitmentVerificationCounterfactual,
  policyIteration,
  type ActionOption,
  type Commitment,
  type CommitmentRef,
  type Planner,
  type PlannerInput,
  type PlannerResult,
} from "../src/index.ts";

const supplier: CommitmentRef = {
  owner: "supplier",
  ledger: "supplier",
  id: "c2",
};

function graph(source: "reported" | "verified" = "reported", verifiedAt?: string): CommitmentGraph {
  const local = new CommitmentLedger([
    {
      id: "deliver",
      subject: "deliver",
      externalDependsOn: [supplier],
    },
  ]);
  const external: Commitment = {
    id: "c2",
    subject: "ship",
    owner: "supplier",
    ledger: "supplier",
    status: "done",
    source,
    verifiedAt: verifiedAt ?? null,
  };
  return new CommitmentGraph(local, [external]);
}

function problem(graphValue: CommitmentGraph): PlannerInput {
  return {
    subject: "deliver",
    at: "2026-11-01T10:00:00Z",
    options: [
      {
        id: "finish",
        verb: "act",
        name: "finish",
        expectedBenefit: 1,
        params: { commitments: { fulfills: ["deliver"], hard: true } },
      },
      {
        id: "wait",
        verb: "wait",
        name: "wait",
        expectedBenefit: 0.1,
      },
    ],
    attributes: { commitment_graph: graphValue },
  };
}

function fixed(actionId: string): Planner {
  return {
    solve: () =>
      ({
        verb: "act",
        confidence: 1,
        reasonCode: "fixed",
        rationale: "fixed",
        actionId,
      }) satisfies PlannerResult,
  };
}

function option(id: string, verb: ActionOption["verb"] = "act"): ActionOption {
  return { id, verb, name: id };
}

describe("decision extensions", () => {
  it("does not trust verified promises without a timestamp", () => {
    assert.equal(
      commitmentTrusted({ id: "c", subject: "s", source: "verified" }),
      false,
    );
  });

  it("proposes a verification decision for a blocked hard option", () => {
    const plan = new CommitmentResolutionPlanner().solve(problem(graph()));

    assert.equal(plan.verb, "verify");
    assert.equal(plan.reasonCode, "commitment_resolution");
    assert.equal(plan.intent?.capability, "verify_commitment");
    const refs = plan.attributes?.verification_refs as Array<Record<string, unknown>>;
    assert.equal(refs[0]?.id, "c2");

    const asked = new CommitmentResolutionPlanner(undefined, {}, { mode: "ask" }).solve(
      problem(graph()),
    );
    assert.equal(asked.verb, "ask");
    assert.equal(asked.requiresApproval, true);
  });

  it("makes composite planners see external blockers", () => {
    assert.notEqual(new LiveCompositePlanner().solve(problem(graph())).actionId, "finish");
    assert.notEqual(new CAVODPlanner().solve(problem(graph())).actionId, "finish");
  });

  it("holds, revises and escalates an earlier decision", () => {
    const held = new RevalidationPlanner(fixed("a")).solve({
      subject: "choose",
      at: "2026-11-01T10:00:00Z",
      options: [option("a")],
      attributes: { previous_action_id: "a" },
    });
    assert.equal(held.reasonCode, "decision_held");
    assert.equal(held.actionId, "a");

    const revised = new RevalidationPlanner(fixed("b")).solve({
      subject: "choose",
      at: "2026-11-01T10:00:00Z",
      options: [option("a")],
      attributes: { previous_action_id: "a" },
    });
    assert.equal(revised.reasonCode, "decision_revised");
    assert.equal(revised.actionId, "b");
  });

  it("selects a planner from a portfolio", () => {
    const portfolio = new PortfolioPlanner(
      { a: fixed("a"), b: fixed("b") },
      { selector: (input) => String(input.attributes?.planner ?? "a") },
    );
    const result = portfolio.solve({
      subject: "choose",
      at: "2026-11-01T10:00:00Z",
      options: [option("a"), option("b")],
      attributes: { planner: "b" },
    });
    assert.equal(result.actionId, "b");
    assert.equal(result.attributes?.planner, "b");
  });

  it("rejects an option outside the downside limit", () => {
    const plan = new RiskBoundedPlanner(undefined, { maxLoss: 0.5 }).solve({
      subject: "choose",
      at: "2026-11-01T10:00:00Z",
      options: [
        {
          id: "safe",
          verb: "act",
          name: "safe",
          expectedBenefit: 0.6,
          params: { risk_bound: { cvar_loss: 0.1 } },
        },
        {
          id: "risky",
          verb: "act",
          name: "risky",
          expectedBenefit: 1,
          params: { risk_bound: { cvar_loss: 0.9 } },
        },
      ],
    });
    assert.equal(plan.actionId, "safe");
    assert.equal(plan.attributes?.cvar_loss, 0.1);
  });

  it("reuses a similar past decision", () => {
    const plan = new CaseBasedPlanner([
      { subject: "send the report", actionId: "send-now" },
    ]).solve({
      subject: "send the report today",
      at: "2026-11-01T10:00:00Z",
      options: [option("send-now"), option("send-later", "wait")],
    });
    assert.equal(plan.actionId, "send-now");
    assert.equal(plan.reasonCode, "case_based");
  });

  it("escalates or resolves a goal conflict", () => {
    const escalated = new ConflictResolutionPlanner().solve({
      subject: "choose",
      at: "2026-11-01T10:00:00Z",
      options: [option("a")],
      attributes: {
        goal_conflicts: [
          { id: "g1", left: "speed", right: "safety", severity: 0.9 },
        ],
      },
    });
    assert.equal(escalated.verb, "escalate");

    const resolved = new ConflictResolutionPlanner().solve({
      subject: "choose",
      at: "2026-11-01T10:00:00Z",
      options: [
        {
          id: "balanced",
          verb: "act",
          name: "balanced",
          params: { resolves: ["g1"] },
        },
      ],
      attributes: { goal_conflicts: [{ id: "g1", severity: 0.9 }] },
    });
    assert.equal(resolved.actionId, "balanced");
  });

  it("finds the verification that changes the decision", () => {
    const result = commitmentVerificationCounterfactual(
      problem(graph()),
      new CommitmentPlanner(),
    );
    assert.equal(result.base_action_id, "wait");
    assert.deepEqual(
      result.flips.map((item) => item.name),
      ["supplier/c2"],
    );
    assert.equal(result.flips[0]?.counterfactual_action_id, "finish");
  });

  it("verifies when the completion probability is low", () => {
    const plan = new CommitmentBeliefPlanner(undefined, {
      defaultProbability: 0.4,
    }).solve(problem(graph()));

    assert.equal(plan.verb, "verify");
    assert.equal(plan.reasonCode, "commitment_belief_verify");
    assert.equal(plan.attributes?.completion_probability, 0.4);
  });

  it("acts when the completion probability is high", () => {
    const base = problem(graph());
    const plan = new CommitmentBeliefPlanner(undefined, {
      defaultProbability: 0.4,
    }).solve({
      ...base,
      attributes: {
        ...base.attributes,
        commitment_probabilities: { "supplier/supplier/c2": 0.9 },
      },
    });

    assert.equal(plan.actionId, "finish");
    assert.equal(plan.attributes?.completion_probability, 0.9);
  });

  it("prefers a certain safe option over an uncertain promise", () => {
    const plan = new CommitmentBeliefPlanner(undefined, {
      defaultProbability: 0.4,
    }).solve({
      subject: "deliver",
      at: "2026-11-01T10:00:00Z",
      options: [
        {
          id: "finish",
          verb: "act",
          name: "finish",
          expectedBenefit: 1,
          params: { commitments: { fulfills: ["deliver"], hard: true } },
        },
        { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6 },
      ],
      attributes: { commitment_graph: graph() },
    });

    assert.equal(plan.actionId, "safe");
    assert.equal(plan.reasonCode, "commitment_belief");
  });

  it("solves a discounted MDP with policy iteration", () => {
    const model = new MdpModel({
      states: ["s0", "s1", "s2"],
      actions: ["go", "stay"],
      transitions: [
        { state: "s0", action: "go", nextState: "s1", probability: 1, reward: 1 },
        { state: "s0", action: "stay", nextState: "s0", probability: 1, reward: 0 },
        { state: "s1", action: "go", nextState: "s2", probability: 1, reward: 2 },
        { state: "s1", action: "stay", nextState: "s1", probability: 1, reward: 0 },
      ],
      start: "s0",
      discount: 0.9,
      horizon: null,
    });
    const result = policyIteration(model);
    assert.equal(result.policy.s0, "go");
    assert.equal(result.policy.s1, "go");
    assert.equal(Math.round(result.values.s0! * 1e6) / 1e6, 2.8);
  });
});
