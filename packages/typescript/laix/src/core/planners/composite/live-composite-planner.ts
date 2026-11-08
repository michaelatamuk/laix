import type { ActionOption } from "../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../contract/planner.ts";
import {
  UtilityPlanner,
  UtilityModel,
  approvalRequired,
  constraintBlocker,
} from "../utility/utility-planner.ts";
import type { RiskAttitude } from "../utility/utility-planner.ts";
import {
  activeCommitments,
  commitmentScoreOption,
} from "../commitment/commitment-planner.ts";
import type { CommitmentWeights } from "../commitment/commitment-planner.ts";
import {
  executionScoreOption,
  receiptStatus,
} from "../execution/execution-planner.ts";
import type { ExecutionWeights } from "../execution/execution-planner.ts";
import {
  approvalState,
  humanAttentionCost,
  humanAttentionScoreOption,
  remainingBudget,
} from "../human-attention/human-attention-planner.ts";
import type { HumanAttentionWeights } from "../human-attention/human-attention-planner.ts";

export interface CompositeScore {
  utility: number;
  commitment: number;
  execution: number;
  human_attention: number;
  total: number;
}

interface LiveOptions {
  commitmentWeights?: CommitmentWeights;
  executionWeights?: ExecutionWeights;
  humanAttentionWeights?: HumanAttentionWeights;
}

interface Row {
  option: ActionOption;
  score: CompositeScore;
  feasible: boolean;
  blocker: string | null;
  commitment: ReturnType<typeof commitmentScoreOption>;
  execution: ReturnType<typeof executionScoreOption>;
  humanAttention: ReturnType<typeof humanAttentionScoreOption>;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class LiveCompositePlanner {
  readonly name = "live.v1";
  readonly model: UtilityModel;
  readonly commitmentWeights: Required<CommitmentWeights>;
  readonly executionWeights: Required<ExecutionWeights>;
  readonly humanAttentionWeights: Required<HumanAttentionWeights>;
  private readonly utility: UtilityPlanner;

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
    this.humanAttentionWeights = {
      interrupt: options.humanAttentionWeights?.interrupt ?? 0.4,
      approval: options.humanAttentionWeights?.approval ?? 0.25,
      escalation: options.humanAttentionWeights?.escalation ?? 0.3,
      exhausted: options.humanAttentionWeights?.exhausted ?? 1.0,
    };
    this.utility = new UtilityPlanner(model);
  }

  solve(problem: PlannerInput): PlannerResult {
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
      const attention = humanAttentionScoreOption(
        option,
        model,
        this.humanAttentionWeights,
        remaining,
        approval,
        approvalState(problem, option),
      );
      const blocker = constraintBlocker(problem, option);
      const score: CompositeScore = {
        utility: commitment.utility,
        commitment: commitment.commitment,
        execution: execution.execution,
        human_attention: attention.human_attention,
        total: round(
          commitment.utility +
            commitment.commitment +
            execution.execution +
            attention.human_attention,
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
        humanAttention: attention,
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
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)}, commitments ${best.score.commitment >= 0 ? "+" : ""}${best.score.commitment.toFixed(3)}, execution ${best.score.execution >= 0 ? "+" : ""}${best.score.execution.toFixed(3)} and attention ${best.score.human_attention >= 0 ? "+" : ""}${best.score.human_attention.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.humanAttention.effect.requiresApproval ||
          best.execution.requiresApproval,
      ),
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        utility: best.score.utility,
        commitment_score: best.score.commitment,
        execution_score: best.score.execution,
        human_attention_score: best.score.human_attention,
        human_attention_cost: humanAttentionCost(best.humanAttention.effect),
        commitments_fulfilled: [...best.commitment.fulfilled],
        commitments_violated: [...best.commitment.violated],
        commitments_created: [...best.commitment.created],
        receipt_status: best.execution.receiptStatus,
        approval_state: best.humanAttention.effect.approvalState,
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
        human_attention: row.score.human_attention,
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

  private wait(reasonCode: string, rationale: string): PlannerResult {
    return { verb: "wait", confidence: 1.0, reasonCode, rationale, score: 0.0 };
  }
}
