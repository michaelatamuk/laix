import type { Intent } from "../../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../../contract/planner.ts";
import {
  CommitmentGraph,
  commitmentKey,
  type CommitmentRef,
} from "../../../domain/commitments/commitments.ts";
import { UtilityModel, UtilityPlanner } from "../utility/utility-planner.ts";
import {
  activeAndGraph,
  commitmentEffect,
} from "./commitment-planner.ts";

function probabilityKey(ref: CommitmentRef): string {
  return `${ref.owner}/${ref.ledger ?? ""}/${ref.id}`;
}

export class CommitmentBeliefPlanner {
  readonly name = "commitment_belief.v1";
  readonly model: UtilityModel;
  readonly defaultProbability: number;
  readonly verifyBelow: number;
  readonly requireVerified: boolean;
  readonly maxVerificationAgeMs?: number;
  private readonly utility: UtilityPlanner;

  constructor(
    model: UtilityModel = new UtilityModel(),
    options: {
      defaultProbability?: number;
      verifyBelow?: number;
      requireVerified?: boolean;
      maxVerificationAgeMs?: number;
    } = {},
  ) {
    this.model = model;
    this.defaultProbability = options.defaultProbability ?? 0.5;
    this.verifyBelow = options.verifyBelow ?? 0.7;
    this.requireVerified = options.requireVerified ?? true;
    this.maxVerificationAgeMs = options.maxVerificationAgeMs;
    if (this.defaultProbability < 0 || this.defaultProbability > 1) {
      throw new Error("defaultProbability must be between zero and one");
    }
    if (this.verifyBelow < 0 || this.verifyBelow > 1) {
      throw new Error("verifyBelow must be between zero and one");
    }
    this.utility = new UtilityPlanner(model);
  }

  solve(problem: PlannerInput): PlannerResult {
    const options = [...(problem.options ?? [])];
    if (!options.length) return this.wait("no_options", "there are no options to score");
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const { active, graph } = activeAndGraph(problem);
    const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
    const now = new Date(problem.at);
    const rows = options.map((option) => {
      const utility = model.score(option);
      const refs: CommitmentRef[] = [];
      for (const commitmentId of commitmentEffect(option).fulfills) {
        const commitment = active.get(commitmentId);
        if (!commitment) continue;
        for (const ref of graph.dependencies(commitment)) {
          if (!refs.some((item) => commitmentKey(item) === commitmentKey(ref))) {
            refs.push(ref);
          }
        }
      }
      const probability = refs.length
        ? Math.min(
            ...refs.map((ref) => this.probability(ref, graph, attributes, now)),
          )
        : 1;
      return {
        option,
        utility: Math.round(utility * 1e6) / 1e6,
        probability: Math.round(probability * 1e6) / 1e6,
        expected: Math.round(utility * probability * 1e6) / 1e6,
        refs,
        feasible: model.feasible(option),
      };
    });
    const feasible = rows.filter((row) => row.feasible);
    if (!feasible.length) {
      return this.wait("no_feasible_option", "every option breaks a hard limit");
    }
    feasible.sort((left, right) =>
      right.expected !== left.expected
        ? right.expected - left.expected
        : left.option.id < right.option.id
          ? -1
          : 1,
    );
    const best = feasible[0]!;
    const second = feasible[1]?.expected;
    if (best.probability < this.verifyBelow && best.refs.length) {
      const refs = best.refs.map((ref) => ({
        owner: ref.owner,
        ledger: ref.ledger ?? null,
        id: ref.id,
        reason: "uncertain",
      }));
      const intent: Intent = { capability: "verify_commitment", args: { refs } };
      return {
        verb: "verify",
        confidence: Math.min(1, Math.max(0, 1 - best.probability)),
        reasonCode: "commitment_belief_verify",
        rationale: `${best.option.id} depends on a promise with completion probability ${best.probability.toFixed(3)}`,
        actionId: "resolve-commitments",
        intent,
        reversible: true,
        attributes: {
          completion_probability: best.probability,
          verification_refs: refs,
        },
      };
    }
    return {
      verb: best.option.verb,
      confidence: this.confidence(best.expected, second),
      reasonCode: "commitment_belief",
      rationale: `${best.option.id} has expected utility ${best.expected.toFixed(3)} at completion probability ${best.probability.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(best.option.requiresApproval),
      reversible: best.option.reversible ?? true,
      score: best.expected,
      alternatives: rows
        .filter((row) => row.option.id !== best.option.id)
        .map((row) => ({
          action_id: row.option.id,
          verb: row.option.verb,
          name: row.option.name,
          utility: row.utility,
          completion_probability: row.probability,
          expected_utility: row.expected,
          rejected_reason_code: row.feasible
            ? "lower_expected_utility"
            : "outside_hard_limits",
        })),
      attributes: {
        utility: best.utility,
        completion_probability: best.probability,
        expected_utility: best.expected,
      },
    };
  }

  private probability(
    ref: CommitmentRef,
    graph: CommitmentGraph,
    attributes: Record<string, unknown>,
    now: Date,
  ): number {
    const item = graph.get(ref);
    if (!item) return 0;
    const trusted =
      item.status === "done" &&
      (item.source ?? "local") !== "reported" &&
      (item.source !== "verified" || item.verifiedAt !== null) &&
      (this.maxVerificationAgeMs === undefined ||
        graph.isFresh(item, now, this.maxVerificationAgeMs));
    if (trusted) return 1;

    const explicit = attributes.commitment_probabilities;
    if (explicit && typeof explicit === "object") {
      const mapping = explicit as Record<string, unknown>;
      for (const key of [
        probabilityKey(ref),
        `${ref.owner}:${ref.id}`,
        ref.id,
      ]) {
        if (mapping[key] !== undefined) {
          const value = Number(mapping[key]);
          if (!Number.isNaN(value)) return Math.min(1, Math.max(0, value));
        }
      }
    }
    const payload = item.payload.completion_probability;
    if (payload !== undefined) {
      const value = Number(payload);
      if (!Number.isNaN(value)) return Math.min(1, Math.max(0, value));
    }
    return this.defaultProbability;
  }

  private confidence(best: number, second: number | undefined): number {
    if (second === undefined) return 1;
    const gap = Math.max(0, best - second);
    return Math.min(1, Math.max(0, 0.5 + 0.5 * (gap / Math.max(Math.abs(best), 1e-9))));
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
        (attributes.risk_attitude as "averse" | "neutral" | "seeking" | undefined) ??
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
