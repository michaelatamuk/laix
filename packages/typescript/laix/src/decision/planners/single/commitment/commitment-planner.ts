import type { ActionOption } from "../../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../../contract/planner.ts";
import type { Commitment } from "../../../domain/commitments/commitments.ts";
import { CommitmentLedger, commitmentDue } from "../../../domain/commitments/commitments.ts";
import {
  UtilityPlanner,
  UtilityModel,
  approvalRequired,
  constraintBlocker,
} from "../utility/utility-planner.ts";
import type { RiskAttitude } from "../utility/utility-planner.ts";

export interface CommitmentWeights {
  keep?: number;
  violate?: number;
  create?: number;
  due?: number;
  blocked?: number;
}

export interface CommitmentEffect {
  fulfills: string[];
  violates: string[];
  creates: string[];
  hard: boolean;
}

export interface CommitmentScore {
  utility: number;
  commitment: number;
  total: number;
  fulfilled: string[];
  violated: string[];
  created: string[];
  dueFulfilled: string[];
  dueViolated: string[];
  blockedFulfilled: string[];
  blocked: string | null;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function ids(value: unknown): string[] {
  if (value === undefined || value === null) return [];
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) {
    return value.map((item) =>
      item !== null && typeof item === "object"
        ? String((item as Record<string, unknown>).id ?? item)
        : String(item),
    );
  }
  if (typeof value === "object") {
    return [String((value as Record<string, unknown>).id ?? value)];
  }
  return [String(value)];
}

function emptyEffect(): CommitmentEffect {
  return { fulfills: [], violates: [], creates: [], hard: false };
}

export function commitmentEffect(option: ActionOption): CommitmentEffect {
  const params = (option.params ?? {}) as Record<string, unknown>;
  const payload = (params.commitments ?? params.commitment ?? params) as Record<
    string,
    unknown
  >;
  if (!payload || typeof payload !== "object") return emptyEffect();
  const pick = (key: string): unknown =>
    payload[key] ?? (payload !== params ? params[key] : undefined);
  return {
    fulfills: ids(pick("fulfills")),
    violates: ids(pick("violates")),
    creates: ids(pick("creates")),
    hard: Boolean(pick("hard")),
  };
}

export function activeCommitments(problem: PlannerInput): Map<string, Commitment> {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const raw = attributes.commitments ?? attributes.commitment_ledger;
  if (raw === undefined || raw === null) return new Map();
  const items =
    raw instanceof CommitmentLedger
      ? raw.all()
      : Array.isArray(raw)
        ? (raw as Commitment[])
        : ((raw as { commitments?: Commitment[] }).commitments ?? []);
  const result = new Map<string, Commitment>();
  for (const item of items) result.set(item.id, item);
  return result;
}

function isBlocked(
  commitmentId: string,
  commitments: Map<string, Commitment>,
): boolean {
  const commitment = commitments.get(commitmentId);
  if (!commitment) return true;
  for (const dependency of commitment.dependsOn ?? []) {
    const item = commitments.get(dependency);
    if (!item || (item.status ?? "open") !== "done") return true;
  }
  return false;
}

export function commitmentScoreOption(
  option: ActionOption,
  model: UtilityModel,
  active: Map<string, Commitment>,
  weights: Required<CommitmentWeights>,
  now: Date,
): CommitmentScore {
  const effect = commitmentEffect(option);
  const openIds = new Set(
    [...active.entries()]
      .filter(([, item]) => (item.status ?? "open") === "open")
      .map(([id]) => id),
  );
  const fulfilled = effect.fulfills.filter(
    (id) => openIds.has(id) && !isBlocked(id, active),
  );
  const blockedFulfilled = effect.fulfills.filter(
    (id) => openIds.has(id) && isBlocked(id, active),
  );
  const violated = effect.violates.filter((id) => openIds.has(id));
  const created = effect.creates.filter((id) => !active.has(id));
  const dueFulfilled = fulfilled.filter((id) => commitmentDue(active.get(id)!, now));
  const dueViolated = violated.filter((id) => commitmentDue(active.get(id)!, now));
  const weightOf = (id: string): number => 0.5 + (active.get(id)?.priority ?? 0.5);
  const commitment =
    weights.keep * fulfilled.reduce((total, id) => total + weightOf(id), 0) +
    weights.due * dueFulfilled.reduce((total, id) => total + weightOf(id), 0) -
    weights.violate * violated.reduce((total, id) => total + weightOf(id), 0) -
    weights.due * dueViolated.reduce((total, id) => total + weightOf(id), 0) -
    weights.blocked * blockedFulfilled.length -
    weights.create * created.length;
  const utility = model.score(option);
  return {
    utility: round(utility),
    commitment: round(commitment),
    total: round(utility + commitment),
    fulfilled,
    violated,
    created,
    dueFulfilled,
    dueViolated,
    blockedFulfilled,
    blocked:
      effect.hard && violated.length
        ? `hard commitment: ${violated.join(", ")}`
        : null,
  };
}

interface Row {
  option: ActionOption;
  score: CommitmentScore;
  feasible: boolean;
  blocker: string | null;
}

export class CommitmentPlanner {
  readonly name = "commitment.v1";
  readonly model: UtilityModel;
  readonly weights: Required<CommitmentWeights>;
  private readonly utility: UtilityPlanner;

  constructor(model: UtilityModel = new UtilityModel(), weights: CommitmentWeights = {}) {
    this.model = model;
    this.weights = {
      keep: weights.keep ?? 0.35,
      violate: weights.violate ?? 1.0,
      create: weights.create ?? 0.1,
      due: weights.due ?? 0.25,
      blocked: weights.blocked ?? 0.5,
    };
    for (const [key, value] of Object.entries(this.weights)) {
      if (value < 0) throw new Error(`commitment weight ${key} must not be negative`);
    }
    this.utility = new UtilityPlanner(model);
  }

  solve(problem: PlannerInput): PlannerResult {
    const options = [...(problem.options ?? [])];
    if (!options.length) {
      return this.wait("no_options", "there are no options to score");
    }
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const active = activeCommitments(problem);
    const now = new Date(problem.at);
    const rows: Row[] = options.map((option) => {
      const score = commitmentScoreOption(option, model, active, this.weights, now);
      const blocker = constraintBlocker(problem, option);
      return {
        option,
        score,
        feasible: model.feasible(option) && blocker === null && score.blocked === null,
        blocker: score.blocked ?? blocker,
      };
    });
    const feasible = rows.filter((row) => row.feasible);
    if (!feasible.length) {
      return this.wait(
        "no_feasible_option",
        "every option breaks a hard limit or a hard commitment",
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
      reasonCode: "commitment_aware",
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)} and commitment score ${best.score.commitment >= 0 ? "+" : ""}${best.score.commitment.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.option.requiresApproval ||
          best.option.destructive ||
          approvalRequired(problem),
      ),
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        utility: best.score.utility,
        commitment_score: best.score.commitment,
        commitments_fulfilled: [...best.score.fulfilled],
        commitments_violated: [...best.score.violated],
        commitments_created: [...best.score.created],
        commitments_due_fulfilled: [...best.score.dueFulfilled],
        commitments_blocked_fulfilled: [...best.score.blockedFulfilled],
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
        total: row.score.total,
        rejected_because: !row.feasible
          ? row.blocker
            ? `blocked by ${row.blocker}`
            : "outside the hard limits"
          : "lower commitment-adjusted score",
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
