import type { ActionOption } from "./contracts.ts";
import type { DecisionProblem, Plan } from "./engine.ts";
import {
  UtilityEngine,
  UtilityModel,
  approvalRequired,
  constraintBlocker,
} from "./utility.ts";
import type { RiskAttitude } from "./utility.ts";
import {
  activeCommitments,
  commitmentScoreOption,
} from "./commitment-planner.ts";
import type { CommitmentWeights } from "./commitment-planner.ts";
import {
  executionScoreOption,
  receiptStatus,
} from "./execution-planner.ts";
import type { ExecutionWeights } from "./execution-planner.ts";
import {
  approvalState,
  attentionScoreOption,
  remainingBudget,
} from "./attention-planner.ts";
import type { AttentionWeights } from "./attention-planner.ts";

export interface LiveScore {
  utility: number;
  commitment: number;
  execution: number;
  attention: number;
  total: number;
}

interface LiveOptions {
  commitmentWeights?: CommitmentWeights;
  executionWeights?: ExecutionWeights;
  attentionWeights?: AttentionWeights;
}

interface Row {
  option: ActionOption;
  score: LiveScore;
  feasible: boolean;
  blocker: string | null;
  commitment: ReturnType<typeof commitmentScoreOption>;
  execution: ReturnType<typeof executionScoreOption>;
  attention: ReturnType<typeof attentionScoreOption>;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class LiveDecisionEngine {
  readonly name = "live.v1";
  readonly model: UtilityModel;
  readonly commitmentWeights: Required<CommitmentWeights>;
  readonly executionWeights: Required<ExecutionWeights>;
  readonly attentionWeights: Required<AttentionWeights>;
  private readonly utility: UtilityEngine;

  constructor(model: UtilityModel = new UtilityModel(), options: LiveOptions = {}) {
    this.model = model;
    this.commitmentWeights = {
      keep: options.commitmentWeights?.keep ?? 0.35,
      violate: options.commitmentWeights?.violate ?? 1.0,
      create: options.commitmentWeights?.create ?? 0.1,
      due: options.commitmentWeights?.due ?? 0.25,
      blocked: options.commitmentWeights?.blocked ?? 0.5,
    };
    this.executionWeights = {
      irreversible: options.executionWeights?.irreversible ?? 0.35,
      unknown: options.executionWeights?.unknown ?? 0.5,
      approval: options.executionWeights?.approval ?? 0.15,
      recovery: options.executionWeights?.recovery ?? 0.25,
    };
    this.attentionWeights = {
      interrupt: options.attentionWeights?.interrupt ?? 0.4,
      approval: options.attentionWeights?.approval ?? 0.25,
      escalation: options.attentionWeights?.escalation ?? 0.3,
      exhausted: options.attentionWeights?.exhausted ?? 1.0,
    };
    this.utility = new UtilityEngine(model);
  }

  solve(problem: DecisionProblem): Plan {
    const options = [...(problem.options ?? [])];
    if (!options.length) {
      return this.wait("no_options", "there are no options to score");
    }
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const commitments = activeCommitments(problem);
    const now = new Date(problem.at);
    const approval = approvalRequired(problem);
    const remaining = remainingBudget(problem);
    const rows: Row[] = options.map((option) => {
      const commitment = commitmentScoreOption(
        option,
        model,
        commitments,
        this.commitmentWeights,
        now,
      );
      const execution = executionScoreOption(
        option,
        model,
        this.executionWeights,
        approval,
        receiptStatus(problem, option),
      );
      const attention = attentionScoreOption(
        option,
        model,
        this.attentionWeights,
        remaining,
        approval,
        approvalState(problem, option),
      );
      const blocker = constraintBlocker(problem, option);
      const score: LiveScore = {
        utility: commitment.utility,
        commitment: commitment.commitment,
        execution: execution.execution,
        attention: attention.attention,
        total: round(
          commitment.utility +
            commitment.commitment +
            execution.execution +
            attention.attention,
        ),
      };
      const blocked = commitment.blocked ?? attention.blocked ?? blocker;
      return {
        option,
        score,
        feasible: model.feasible(option) && blocked === null,
        blocker: blocked,
        commitment,
        execution,
        attention,
      };
    });
    const feasible = rows.filter((row) => row.feasible);
    if (!feasible.length) {
      return this.wait(
        "no_feasible_option",
        "every option breaks a hard limit or an attention constraint",
      );
    }
    feasible.sort((left, right) =>
      right.score.total !== left.score.total
        ? right.score.total - left.score.total
        : left.option.id < right.option.id
          ? -1
          : 1,
    );
    const best = feasible[0]!;
    const second = feasible[1]?.score.total;
    return {
      verb: best.option.verb,
      confidence: this.confidence(best.score.total, second),
      reasonCode: "live_decision",
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)}, commitments ${best.score.commitment >= 0 ? "+" : ""}${best.score.commitment.toFixed(3)}, execution ${best.score.execution >= 0 ? "+" : ""}${best.score.execution.toFixed(3)} and attention ${best.score.attention >= 0 ? "+" : ""}${best.score.attention.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.attention.effect.requiresApproval ||
          best.execution.requiresApproval,
      ),
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        utility: best.score.utility,
        commitment_score: best.score.commitment,
        execution_score: best.score.execution,
        attention_score: best.score.attention,
        commitments_fulfilled: [...best.commitment.fulfilled],
        commitments_violated: [...best.commitment.violated],
        commitments_created: [...best.commitment.created],
        receipt_status: best.execution.receiptStatus,
        approval_state: best.attention.effect.approvalState,
      },
    };
  }

  private modelFor(attributes: Record<string, unknown>): UtilityModel {
    if (
      attributes.max_risk === undefined &&
      attributes.max_cost === undefined &&
      attributes.max_latency_ms === undefined &&
      attributes.risk_attitude === undefined
    ) {
      return this.model;
    }
    return new UtilityModel({
      weights: this.model.weights,
      riskAttitude:
        (attributes.risk_attitude as RiskAttitude | undefined) ?? this.model.riskAttitude,
      maxRisk:
        attributes.max_risk === undefined ? this.model.maxRisk : Number(attributes.max_risk),
      maxCost:
        attributes.max_cost === undefined ? this.model.maxCost : Number(attributes.max_cost),
      maxLatencyMs:
        attributes.max_latency_ms === undefined
          ? this.model.maxLatencyMs
          : Number(attributes.max_latency_ms),
    });
  }

  private alternatives(rows: Row[], bestId: string): Array<Record<string, unknown>> {
    return rows
      .filter((row) => row.option.id !== bestId)
      .map((row) => ({
        action_id: row.option.id,
        verb: row.option.verb,
        name: row.option.name,
        utility: row.score.utility,
        commitment: row.score.commitment,
        execution: row.score.execution,
        attention: row.score.attention,
        total: row.score.total,
        rejected_because: row.blocker
          ? `blocked by ${row.blocker}`
          : !row.feasible
            ? "outside the hard limits"
            : "lower integrated score",
      }))
      .sort((left, right) =>
        Number(right.total) !== Number(left.total)
          ? Number(right.total) - Number(left.total)
          : String(left.action_id) < String(right.action_id)
            ? -1
            : 1,
      );
  }

  private confidence(best: number, second: number | undefined): number {
    if (second === undefined) return 1.0;
    const gap = Math.max(0, best - second);
    return Math.min(1, Math.max(0, 0.5 + 0.5 * (gap / Math.max(Math.abs(best), 1e-9))));
  }

  private wait(reasonCode: string, rationale: string): Plan {
    return { verb: "wait", confidence: 1.0, reasonCode, rationale, score: 0.0 };
  }
}
