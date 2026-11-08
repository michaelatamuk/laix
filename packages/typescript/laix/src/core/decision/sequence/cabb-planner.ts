import type { ActionOption } from "../../contracts.ts";
import type { Commitment, CommitmentStatus } from "../../commitments/commitments.ts";
import { UtilityModel } from "../single/planners/utility/utility-planner.ts";
import { commitmentScoreOption } from "../single/planners/commitment/commitment-planner.ts";
import type { CommitmentWeights } from "../single/planners/commitment/commitment-planner.ts";
import { executionScoreOption } from "../single/planners/execution/execution-planner.ts";
import type { ExecutionWeights } from "../single/planners/execution/execution-planner.ts";
import { humanAttentionScoreOption } from "../single/planners/human-attention/human-attention-planner.ts";
import type { HumanAttentionWeights } from "../single/planners/human-attention/human-attention-planner.ts";
import type {
  DecisionPlan,
  DecisionScenario,
  DecisionStep,
} from "./contract.ts";

interface Scored {
  option: ActionOption;
  immediate: number;
  remaining: number;
  fulfilled: string[];
  violated: string[];
  blocked: boolean;
}

interface Best {
  score: number;
  actions: string[];
  remaining: number;
  violations: string[];
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function statusesOf(scenario: DecisionScenario): Map<string, CommitmentStatus> {
  return new Map<string, CommitmentStatus>(
    (scenario.commitments ?? []).map((item) => [item.id, item.status ?? "open"]),
  );
}

export class CABBPlanner {
  readonly name = "cabb.v1";
  readonly model: UtilityModel;
  readonly commitmentWeights: Required<CommitmentWeights>;
  readonly executionWeights: Required<ExecutionWeights>;
  readonly humanAttentionWeights: Required<HumanAttentionWeights>;

  constructor(
    model: UtilityModel = new UtilityModel(),
    options: {
      commitmentWeights?: CommitmentWeights;
      executionWeights?: ExecutionWeights;
      humanAttentionWeights?: HumanAttentionWeights;
    } = {},
  ) {
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
  }

  plan(scenario: DecisionScenario): DecisionPlan {
    if (!scenario.steps.length) {
      return { actions: [], score: 0, attentionSpent: 0, violations: [], nodes: 0, optimal: true };
    }
    const statuses = statusesOf(scenario);
    const initialAttention = this.initialAttention(scenario);
    const finalAt = new Date(scenario.steps.at(-1)!.at);
    const commitmentCeiling = (scenario.commitments ?? []).reduce(
      (total, item) =>
        total +
        this.commitmentWeights.keep * (0.5 + (item.priority ?? 0.5)) +
        this.commitmentWeights.due * (0.5 + (item.priority ?? 0.5)),
      0,
    );
    const bounds = scenario.steps.map((step) =>
      this.relaxedBound(step, commitmentCeiling),
    );
    const best: Best = {
      score: Number.NEGATIVE_INFINITY,
      actions: [],
      remaining: initialAttention,
      violations: [],
    };
    let nodes = 0;

    const search = (
      index: number,
      current: Map<string, CommitmentStatus>,
      remaining: number,
      score: number,
      actions: string[],
      violations: string[],
    ): void => {
      nodes += 1;
      if (index === scenario.steps.length) {
        const total = score - this.terminalPenalty(scenario, current, finalAt);
        if (total > best.score) {
          best.score = total;
          best.actions = [...actions];
          best.remaining = remaining;
          best.violations = [...violations];
        }
        return;
      }
      if (
        score +
          bounds.slice(index).reduce((total, value) => total + value, 0) <=
        best.score
      ) {
        return;
      }
      const step = scenario.steps[index]!;
      const now = new Date(step.at);
      for (const option of step.options) {
        const scored = this.score(scenario, option, current, remaining, now);
        if (scored.blocked) continue;
        search(
          index + 1,
          this.apply(current, scored),
          scored.remaining,
          score + scored.immediate,
          [...actions, option.id],
          [...violations, ...scored.violated],
        );
      }
    };

    search(0, statuses, initialAttention, 0, [], []);
    if (best.score === Number.NEGATIVE_INFINITY) {
      return { actions: [], score: 0, attentionSpent: 0, violations: [], nodes, optimal: true };
    }
    return {
      actions: best.actions,
      score: round(best.score),
      attentionSpent: Number.isFinite(initialAttention)
        ? round(initialAttention - best.remaining)
        : 0,
      violations: best.violations,
      nodes,
      optimal: true,
    };
  }

  evaluate(scenario: DecisionScenario, actions: string[]): DecisionPlan {
    if (actions.length !== scenario.steps.length) {
      throw new Error("actions must match the number of steps");
    }
    if (!scenario.steps.length) {
      return { actions: [], score: 0, attentionSpent: 0, violations: [], nodes: 0, optimal: false };
    }
    const statuses = statusesOf(scenario);
    const initialAttention = this.initialAttention(scenario);
    const finalAt = new Date(scenario.steps.at(-1)!.at);
    let remaining = initialAttention;
    let score = 0;
    const violations: string[] = [];
    for (let index = 0; index < scenario.steps.length; index += 1) {
      const step = scenario.steps[index]!;
      const actionId = actions[index]!;
      const option = step.options.find((item) => item.id === actionId);
      if (!option) {
        throw new Error(`unknown action ${JSON.stringify(actionId)} at ${step.at}`);
      }
      const scored = this.score(scenario, option, statuses, remaining, new Date(step.at));
      if (scored.blocked) {
        throw new Error(`action ${JSON.stringify(actionId)} is blocked at ${step.at}`);
      }
      score += scored.immediate;
      this.applyInPlace(statuses, scored);
      violations.push(...scored.violated);
      remaining = scored.remaining;
    }
    const penalty = this.terminalPenalty(scenario, statuses, finalAt);
    return {
      actions: [...actions],
      score: round(score - penalty),
      attentionSpent: Number.isFinite(initialAttention)
        ? round(initialAttention - remaining)
        : 0,
      violations,
      nodes: 0,
      optimal: false,
    };
  }

  greedyActions(scenario: DecisionScenario, prefix: readonly string[] = []): string[] {
    if (prefix.length > scenario.steps.length) {
      throw new Error("the prefix is longer than the scenario");
    }
    const statuses = statusesOf(scenario);
    let remaining = this.initialAttention(scenario);
    const actions = [...prefix];
    for (let index = 0; index < prefix.length; index += 1) {
      const step = scenario.steps[index]!;
      const actionId = prefix[index]!;
      const option = step.options.find((item) => item.id === actionId);
      if (!option) {
        throw new Error(`unknown action ${JSON.stringify(actionId)} at ${step.at}`);
      }
      const scored = this.score(scenario, option, statuses, remaining, new Date(step.at));
      this.applyInPlace(statuses, scored);
      remaining = scored.remaining;
    }
    for (let index = prefix.length; index < scenario.steps.length; index += 1) {
      const step = scenario.steps[index]!;
      const now = new Date(step.at);
      let chosen: Scored | null = null;
      for (const option of step.options) {
        const scored = this.score(scenario, option, statuses, remaining, now);
        if (scored.blocked) continue;
        if (
          chosen === null ||
          scored.immediate > chosen.immediate ||
          (scored.immediate === chosen.immediate && option.id < chosen.option.id)
        ) {
          chosen = scored;
        }
      }
      if (chosen === null) break;
      actions.push(chosen.option.id);
      this.applyInPlace(statuses, chosen);
      remaining = chosen.remaining;
    }
    return actions;
  }

  advance(
    scenario: DecisionScenario,
    actions: readonly string[],
  ): { commitments: Commitment[]; remaining: number } {
    if (actions.length > scenario.steps.length) {
      throw new Error("the prefix is longer than the scenario");
    }
    const statuses = statusesOf(scenario);
    let remaining = this.initialAttention(scenario);
    for (let index = 0; index < actions.length; index += 1) {
      const step = scenario.steps[index]!;
      const actionId = actions[index]!;
      const option = step.options.find((item) => item.id === actionId);
      if (!option) {
        throw new Error(`unknown action ${JSON.stringify(actionId)} at ${step.at}`);
      }
      const scored = this.score(scenario, option, statuses, remaining, new Date(step.at));
      this.applyInPlace(statuses, scored);
      remaining = scored.remaining;
    }
    return {
      commitments: (scenario.commitments ?? []).map((item) => ({
        ...item,
        status: statuses.get(item.id) ?? item.status ?? "open",
      })),
      remaining,
    };
  }

  private score(
    scenario: DecisionScenario,
    option: ActionOption,
    statuses: Map<string, CommitmentStatus>,
    remaining: number,
    now: Date,
  ): Scored {
    const active = new Map<string, Commitment>();
    for (const item of scenario.commitments ?? []) {
      active.set(item.id, {
        ...item,
        status: statuses.get(item.id) ?? item.status ?? "open",
      });
    }
    const commitment = commitmentScoreOption(
      option,
      this.model,
      active,
      this.commitmentWeights,
      now,
    );
    const execution = executionScoreOption(
      option,
      this.model,
      this.executionWeights,
      false,
      null,
    );
    const attention = humanAttentionScoreOption(
      option,
      this.model,
      this.humanAttentionWeights,
      remaining,
      false,
      null,
    );
    return {
      option,
      immediate:
        commitment.utility +
        commitment.commitment +
        execution.execution +
        attention.human_attention,
      remaining: attention.remaining,
      fulfilled: [...commitment.fulfilled],
      violated: [...commitment.violated],
      blocked: Boolean(commitment.blocked ?? attention.blocked),
    };
  }

  private apply(
    statuses: Map<string, CommitmentStatus>,
    scored: Scored,
  ): Map<string, CommitmentStatus> {
    const updated = new Map(statuses);
    this.applyInPlace(updated, scored);
    return updated;
  }

  private applyInPlace(
    statuses: Map<string, CommitmentStatus>,
    scored: Scored,
  ): void {
    for (const commitmentId of scored.fulfilled) statuses.set(commitmentId, "done");
    for (const commitmentId of scored.violated) statuses.set(commitmentId, "cancelled");
  }

  private initialAttention(scenario: DecisionScenario): number {
    return scenario.humanAttentionBudget?.remaining() ?? Number.POSITIVE_INFINITY;
  }

  private terminalPenalty(
    scenario: DecisionScenario,
    statuses: Map<string, CommitmentStatus>,
    finalAt: Date,
  ): number {
    const commitments = new Map(
      (scenario.commitments ?? []).map((item) => [item.id, item]),
    );
    const openPenalty = scenario.openPenalty ?? 0.5;
    let penalty = 0;
    for (const [commitmentId, status] of statuses.entries()) {
      if (status !== "open") continue;
      const item = commitments.get(commitmentId);
      if (!item) continue;
      const due = item.due ? new Date(item.due) : null;
      if (!due || due.getTime() <= finalAt.getTime()) {
        penalty += openPenalty * (0.5 + (item.priority ?? 0.5));
      }
    }
    return penalty;
  }

  private relaxedBound(step: DecisionStep, commitmentCeiling: number): number {
    if (!step.options.length) return 0;
    return (
      Math.max(...step.options.map((option) => this.model.score(option))) +
      commitmentCeiling
    );
  }
}

export function planDecisions(
  scenario: DecisionScenario,
  options: {
    model?: UtilityModel;
    commitmentWeights?: CommitmentWeights;
    executionWeights?: ExecutionWeights;
    humanAttentionWeights?: HumanAttentionWeights;
  } = {},
): DecisionPlan {
  return new CABBPlanner(options.model, options).plan(scenario);
}
