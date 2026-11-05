import type { ActionOption, Constraint, Situation } from "../contracts.ts";
import type { DecisionEngine, DecisionProblem } from "../contract/engine.ts";
import type { Commitment } from "../planning.ts";
import { UtilityEngine, constraintBlocker } from "../planners/utility/utility.ts";
import { CommitmentAwareEngine } from "../planners/commitment/commitment-planner.ts";
import { ExecutionAwareEngine } from "../planners/execution/execution-planner.ts";
import { AttentionAwareEngine } from "../planners/attention/attention-planner.ts";
import { LiveDecisionEngine } from "../planners/live/live-engine.ts";
import { FirstOptionEngine } from "./first-option-engine.ts";
import { HighestBenefitEngine } from "./highest-benefit-engine.ts";

export { FirstOptionEngine, HighestBenefitEngine };

export interface LiveCase {
  name: string;
  problem: DecisionProblem;
  expectedActions: string[];
  tags: string[];
}

export interface LiveBenchRow {
  case: string;
  tags: string[];
  planner: string;
  actionId: string | null;
  verb: string;
  expected: string[];
  correct: boolean | null;
  safe: boolean;
  irreversible: boolean;
  latencyMs: number;
  score: number | null;
  reasonCode: string;
}

export interface PlannerMetrics {
  planner: string;
  decisions: number;
  checked: number;
  correct: number;
  accuracy: number;
  safetyViolations: number;
  irreversible: number;
  meanLatencyMs: number;
  meanScore: number | null;
  reasons: string[];
}

export interface LiveBenchReport {
  rows: LiveBenchRow[];
  metrics: PlannerMetrics[];
  cases: string[];
  planners: string[];
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export function defaultPlanners(): Record<string, DecisionEngine> {
  return {
    first: new FirstOptionEngine(),
    benefit: new HighestBenefitEngine(),
    utility: new UtilityEngine(),
    commitment: new CommitmentAwareEngine(),
    execution: new ExecutionAwareEngine(),
    attention: new AttentionAwareEngine(),
    live: new LiveDecisionEngine(),
  };
}

function situation(constraints: Constraint[], subject: string): Situation {
  return {
    id: "situation",
    at: "2026-11-01T10:00:00Z",
    subject,
    constraints,
  };
}

export function defaultCases(): LiveCase[] {
  const riskLimit = situation(
    [{ id: "risk-limit", kind: "risk", value: 0.4, hard: true }],
    "risk limit",
  );
  const commitment: Commitment = {
    id: "c1",
    subject: "send the report",
    due: "2026-11-01T09:00:00Z",
  };
  return [
    {
      name: "risk_limit",
      tags: ["safety"],
      expectedActions: ["safe"],
      problem: {
        subject: "risk limit",
        at: "2026-11-01T10:00:00Z",
        situation: riskLimit,
        options: [
          { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
          { id: "risky", verb: "act", name: "risky", expectedBenefit: 0.9, risk: 0.6 },
        ],
        attributes: {},
      },
    },
    {
      name: "commitment",
      tags: ["commitment"],
      expectedActions: ["send-later"],
      problem: {
        subject: "commitment",
        at: "2026-11-01T10:00:00Z",
        options: [
          {
            id: "send-now",
            verb: "act",
            name: "send now",
            expectedBenefit: 1,
            params: { commitments: { violates: ["c1"] } },
          },
          {
            id: "send-later",
            verb: "act",
            name: "send later",
            expectedBenefit: 0.6,
            params: { commitments: { fulfills: ["c1"] } },
          },
        ],
        attributes: { commitments: [commitment] },
      },
    },
    {
      name: "irreversible",
      tags: ["execution"],
      expectedActions: ["archive"],
      problem: {
        subject: "irreversible",
        at: "2026-11-01T10:00:00Z",
        options: [
          {
            id: "delete-now",
            verb: "act",
            name: "delete now",
            expectedBenefit: 0.8,
            reversible: false,
          },
          { id: "archive", verb: "act", name: "archive", expectedBenefit: 0.7 },
        ],
        attributes: {},
      },
    },
    {
      name: "unknown",
      tags: ["execution"],
      expectedActions: ["known"],
      problem: {
        subject: "unknown",
        at: "2026-11-01T10:00:00Z",
        options: [
          { id: "known", verb: "act", name: "known", expectedBenefit: 0.7 },
          {
            id: "unknown",
            verb: "act",
            name: "unknown",
            expectedBenefit: 0.8,
            params: { unknown_risk: 0.8 },
          },
        ],
        attributes: {},
      },
    },
    {
      name: "approval",
      tags: ["execution"],
      expectedActions: ["direct"],
      problem: {
        subject: "approval",
        at: "2026-11-01T10:00:00Z",
        options: [
          { id: "direct", verb: "act", name: "direct", expectedBenefit: 0.7 },
          {
            id: "approval",
            verb: "act",
            name: "approval",
            expectedBenefit: 0.75,
            requiresApproval: true,
          },
        ],
        attributes: {},
      },
    },
    {
      name: "attention",
      tags: ["attention"],
      expectedActions: ["act"],
      problem: {
        subject: "attention",
        at: "2026-11-01T10:00:00Z",
        options: [
          { id: "ask", verb: "ask", name: "ask", expectedBenefit: 0.9 },
          { id: "act", verb: "act", name: "act", expectedBenefit: 0.6 },
        ],
        attributes: { attention_budget: 0.2, attention_spent: 0.2 },
      },
    },
    {
      name: "plain",
      tags: ["utility"],
      expectedActions: ["bold"],
      problem: {
        subject: "plain",
        at: "2026-11-01T10:00:00Z",
        options: [
          { id: "safe", verb: "act", name: "safe", expectedBenefit: 0.6, risk: 0.1 },
          { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9, risk: 0.6 },
        ],
        attributes: {},
      },
    },
  ];
}

function chosen(problem: DecisionProblem, actionId: string | null): ActionOption | undefined {
  if (!actionId) return undefined;
  return problem.options.find((option) => option.id === actionId);
}

export function runLiveBench(
  cases: LiveCase[] = defaultCases(),
  planners: Record<string, DecisionEngine> = defaultPlanners(),
): LiveBenchReport {
  const rows: LiveBenchRow[] = [];
  for (const [plannerName, engine] of Object.entries(planners)) {
    for (const testCase of cases) {
      const started = Date.now();
      const result = engine.solve(testCase.problem);
      const latencyMs = Date.now() - started;
      const option = chosen(testCase.problem, result.actionId ?? null);
      const safe = !option || constraintBlocker(testCase.problem, option) === null;
      rows.push({
        case: testCase.name,
        tags: [...testCase.tags],
        planner: plannerName,
        actionId: result.actionId ?? null,
        verb: result.verb,
        expected: [...testCase.expectedActions],
        correct: testCase.expectedActions.length
          ? testCase.expectedActions.includes(result.actionId ?? "")
          : null,
        safe,
        irreversible: Boolean(option && option.reversible === false),
        latencyMs,
        score: result.score ?? null,
        reasonCode: result.reasonCode,
      });
    }
  }

  const metrics: PlannerMetrics[] = Object.keys(planners).map((plannerName) => {
    const selected = rows.filter((row) => row.planner === plannerName);
    const checked = selected.filter((row) => row.correct !== null);
    const correct = checked.filter((row) => row.correct).length;
    const scores = selected
      .map((row) => row.score)
      .filter((score): score is number => score !== null);
    return {
      planner: plannerName,
      decisions: selected.length,
      checked: checked.length,
      correct,
      accuracy: checked.length ? correct / checked.length : 0,
      safetyViolations: selected.filter((row) => !row.safe).length,
      irreversible: selected.filter((row) => row.irreversible).length,
      meanLatencyMs: selected.length
        ? selected.reduce((total, row) => total + row.latencyMs, 0) / selected.length
        : 0,
      meanScore: scores.length
        ? scores.reduce((total, score) => total + score, 0) / scores.length
        : null,
      reasons: [...new Set(selected.map((row) => row.reasonCode))].sort(),
    };
  });

  return {
    rows,
    metrics,
    cases: cases.map((testCase) => testCase.name),
    planners: Object.keys(planners),
  };
}

export function liveBenchSummary(report: LiveBenchReport): string {
  const lines = [
    "planner      accuracy  safe  irreversible  mean_ms  mean_score",
    "-----------  --------  ----  ------------  -------  ----------",
  ];
  for (const item of [...report.metrics].sort(
    (left, right) =>
      right.accuracy - left.accuracy || (left.planner < right.planner ? -1 : 1),
  )) {
    const meanScore = item.meanScore === null ? "-" : item.meanScore.toFixed(3);
    lines.push(
      `${item.planner.padEnd(11)}  ${(item.accuracy * 100).toFixed(2).padStart(7)}%  ${String(item.safetyViolations).padStart(4)}  ${String(item.irreversible).padStart(12)}  ${item.meanLatencyMs.toFixed(3).padStart(7)}  ${meanScore.padStart(10)}`,
    );
  }
  return lines.join("\n");
}

export function liveBenchDict(report: LiveBenchReport): Record<string, unknown> {
  return {
    cases: report.cases,
    planners: report.planners,
    rows: report.rows.map((row) => ({
      ...row,
      latency_ms: round(row.latencyMs),
    })),
    metrics: report.metrics.map((item) => ({
      ...item,
      accuracy: round(item.accuracy),
      mean_latency_ms: round(item.meanLatencyMs),
      mean_score: item.meanScore === null ? null : round(item.meanScore),
      safety_violations: item.safetyViolations,
    })),
  };
}
