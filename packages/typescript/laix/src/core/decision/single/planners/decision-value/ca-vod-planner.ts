import type { ActionOption } from "../../../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../../../contract/planner.ts";
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
  humanAttentionScoreOption,
  remainingBudget,
} from "../human-attention/human-attention-planner.ts";
import type { HumanAttentionWeights } from "../human-attention/human-attention-planner.ts";
import { PomdpModel } from "../pomdp/pomdp-model.ts";
import {
  actionFutureValue,
  beliefEntropy,
  beliefFromState,
  normalizeBelief,
} from "../pomdp/pomdp-planner.ts";
import type { BeliefState } from "../pomdp/pomdp-planner.ts";
import type { CAVODScore } from "./ca-vod-score.ts";
import type { CAVODWeights } from "./ca-vod-weights.ts";

export type { CAVODScore } from "./ca-vod-score.ts";
export type { CAVODWeights } from "./ca-vod-weights.ts";

interface Row {
  option: ActionOption;
  score: CAVODScore;
  feasible: boolean;
  blocker: string | null;
  commitment: ReturnType<typeof commitmentScoreOption>;
  execution: ReturnType<typeof executionScoreOption>;
  humanAttention: ReturnType<typeof humanAttentionScoreOption>;
}

const INFORMATION_GAIN: Record<string, number> = {
  ask: 0.7,
  verify: 0.5,
  observe: 0.4,
};

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function decisionValue(option: ActionOption): Record<string, unknown> {
  const params = (option.params ?? {}) as Record<string, unknown>;
  const payload = params.decision_value ?? params.value ?? {};
  return payload && typeof payload === "object"
    ? (payload as Record<string, unknown>)
    : {};
}

function uncertainty(problem: PlannerInput, weights: Required<CAVODWeights>): number {
  const raw = (problem.attributes ?? {}).uncertainty;
  if (raw !== undefined) {
    const value = Number(raw);
    if (!Number.isNaN(value)) return Math.min(1, Math.max(0, value));
  }
  return Math.min(1, Math.max(0, weights.uncertainty));
}

function informationValue(
  option: ActionOption,
  value: number,
  weights: Required<CAVODWeights>,
): number {
  const payload = decisionValue(option);
  const explicit = payload.information_value;
  if (explicit !== undefined) {
    const parsed = Number(explicit);
    if (!Number.isNaN(parsed)) return round(Math.max(0, parsed));
  }
  const gain = Number(payload.information_gain ?? INFORMATION_GAIN[option.verb] ?? 0);
  return round(weights.information * value * Math.max(0, Number.isNaN(gain) ? 0 : gain));
}

function optionValue(
  option: ActionOption,
  value: number,
  weights: Required<CAVODWeights>,
): number {
  if (option.verb !== "wait") return 0;
  const payload = decisionValue(option);
  const explicit = payload.option_value;
  if (explicit !== undefined) {
    const parsed = Number(explicit);
    if (!Number.isNaN(parsed)) return round(Math.max(0, parsed));
  }
  return round(weights.waiting * value);
}

export class CAVODPlanner {
  readonly name = "ca_vod.v1";
  readonly model: UtilityModel;
  readonly weights: Required<CAVODWeights>;
  readonly commitmentWeights: Required<CommitmentWeights>;
  readonly executionWeights: Required<ExecutionWeights>;
  readonly humanAttentionWeights: Required<HumanAttentionWeights>;
  readonly pomdpModel: PomdpModel | null;
  readonly belief: BeliefState;
  private readonly utility: UtilityPlanner;
  private readonly enforceFeasibility: boolean;

  constructor(
    model: UtilityModel = new UtilityModel(),
    options: {
      pomdpModel?: PomdpModel;
      belief?: BeliefState;
      weights?: CAVODWeights;
      commitmentWeights?: CommitmentWeights;
      executionWeights?: ExecutionWeights;
      humanAttentionWeights?: HumanAttentionWeights;
      enforceFeasibility?: boolean;
    } = {},
  ) {
    this.model = model;
    this.pomdpModel = options.pomdpModel ?? null;
    this.belief = { ...(options.belief ?? {}) };
    this.weights = {
      information: options.weights?.information ?? 0.5,
      waiting: options.weights?.waiting ?? 0.25,
      uncertainty: options.weights?.uncertainty ?? 0.5,
      future: options.weights?.future ?? 1.0,
    };
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
    this.enforceFeasibility = options.enforceFeasibility ?? true;
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
    const uncertaintyValue = uncertainty(problem, this.weights);
    const belief = this.pomdpModel ? this.resolveBelief(problem) : {};
    const horizon = this.pomdpModel
      ? Number((problem.attributes ?? {}).horizon ?? this.pomdpModel.horizon)
      : 0;
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
      const information = informationValue(option, uncertaintyValue, this.weights);
      const optionTerm = optionValue(option, uncertaintyValue, this.weights);
      const future = this.futureValue(option, belief, horizon);
      const blocker = constraintBlocker(problem, option);
      const score: CAVODScore = {
        utility: commitment.utility,
        commitment: commitment.commitment,
        execution: execution.execution,
        human_attention: attention.human_attention,
        information,
        option: optionTerm,
        future,
        total: round(
          commitment.utility +
            commitment.commitment +
            execution.execution +
            attention.human_attention +
            information +
            optionTerm +
            future,
        ),
      };
      const blocked = commitment.blocked ?? attention.blocked ?? blocker;
      return {
        option,
        score,
        feasible: this.enforceFeasibility
          ? model.feasible(option) && blocked === null
          : true,
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
      reasonCode: "value_of_decision",
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)}, commitment ${best.score.commitment >= 0 ? "+" : ""}${best.score.commitment.toFixed(3)}, execution ${best.score.execution >= 0 ? "+" : ""}${best.score.execution.toFixed(3)}, attention ${best.score.human_attention >= 0 ? "+" : ""}${best.score.human_attention.toFixed(3)}, information ${best.score.information >= 0 ? "+" : ""}${best.score.information.toFixed(3)}, option value ${best.score.option >= 0 ? "+" : ""}${best.score.option.toFixed(3)} and future value ${best.score.future >= 0 ? "+" : ""}${best.score.future.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.humanAttention.effect.requiresApproval ||
          best.execution.requiresApproval,
      ),
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        algorithm: this.name,
        utility: best.score.utility,
        commitment_score: best.score.commitment,
        execution_score: best.score.execution,
        human_attention_score: best.score.human_attention,
        information_value: best.score.information,
        option_value: best.score.option,
        future_value: best.score.future,
        uncertainty: uncertaintyValue,
        belief: Object.keys(belief).length ? belief : null,
        belief_entropy: Object.keys(belief).length ? beliefEntropy(belief) : null,
        horizon: this.pomdpModel ? horizon : null,
        commitments_fulfilled: [...best.commitment.fulfilled],
        commitments_violated: [...best.commitment.violated],
        commitments_created: [...best.commitment.created],
        receipt_status: best.execution.receiptStatus,
        approval_state: best.humanAttention.effect.approvalState,
      },
    };
  }

  private resolveBelief(problem: PlannerInput): BeliefState {
    if (!this.pomdpModel) return {};
    const raw = (problem.attributes ?? {}).belief;
    if (raw && typeof raw === "object" && !Array.isArray(raw)) {
      return normalizeBelief(raw as BeliefState, this.pomdpModel.states);
    }
    if (Object.keys(this.belief).length) {
      return normalizeBelief(this.belief, this.pomdpModel.states);
    }
    const state = (problem.attributes ?? {}).state;
    if (typeof state === "string" && state) {
      return beliefFromState(state, this.pomdpModel.states);
    }
    const size = this.pomdpModel.states.length;
    return Object.fromEntries(
      this.pomdpModel.states.map((item) => [item, 1 / size]),
    );
  }

  private actionFor(option: ActionOption): string | null {
    if (!this.pomdpModel) return null;
    if (this.pomdpModel.actions.includes(option.id)) return option.id;
    if (this.pomdpModel.actions.includes(option.verb)) return option.verb;
    return null;
  }

  private futureValue(
    option: ActionOption,
    belief: BeliefState,
    horizon: number,
  ): number {
    if (!this.pomdpModel || !Object.keys(belief).length) return 0;
    const action = this.actionFor(option);
    if (!action) return 0;
    if (
      !Object.keys(belief).some((state) =>
        this.pomdpModel!.actionAvailable(state, action),
      )
    ) {
      return 0;
    }
    return round(
      this.weights.future *
        actionFutureValue(this.pomdpModel, belief, action, { horizon }),
    );
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
        (attributes.risk_attitude as RiskAttitude | undefined) ??
        this.model.riskAttitude,
      maxRisk:
        attributes.max_risk === undefined
          ? this.model.maxRisk
          : Number(attributes.max_risk),
      maxCost:
        attributes.max_cost === undefined
          ? this.model.maxCost
          : Number(attributes.max_cost),
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
        information: row.score.information,
        option: row.score.option,
        future: row.score.future,
        total: row.score.total,
        rejected_because: row.blocker
          ? `blocked by ${row.blocker}`
          : row.feasible
            ? "lower value of decision"
            : "outside the hard limits",
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
    if (second === undefined) return 1;
    const gap = Math.max(0, best - second);
    return Math.min(1, Math.max(0, 0.5 + 0.5 * (gap / Math.max(Math.abs(best), 1e-9))));
  }

  private wait(reasonCode: string, rationale: string): PlannerResult {
    return {
      verb: "wait",
      confidence: 1,
      reasonCode,
      rationale,
      score: 0,
    };
  }
}
