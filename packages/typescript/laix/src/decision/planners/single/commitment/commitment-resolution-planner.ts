import type { Intent } from "../../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../../contract/planner.ts";
import type { UtilityModel } from "../utility/utility-planner.ts";
import {
  CommitmentPlanner,
  activeAndGraph,
  optionBlockers,
  type CommitmentBlock,
  type CommitmentWeights,
} from "./commitment-planner.ts";

export class CommitmentResolutionPlanner {
  readonly name = "commitment.resolution.v1";
  readonly mode: "verify" | "ask";
  private readonly planner: CommitmentPlanner;

  constructor(
    model?: UtilityModel,
    weights: CommitmentWeights = {},
    options: {
      requireVerified?: boolean;
      maxVerificationAgeMs?: number;
      mode?: "verify" | "ask";
    } = {},
  ) {
    this.mode = options.mode ?? "verify";
    if (this.mode !== "verify" && this.mode !== "ask") {
      throw new Error(`unknown commitment resolution mode: ${this.mode}`);
    }
    this.planner = new CommitmentPlanner(model, weights, {
      requireVerified: options.requireVerified,
      maxVerificationAgeMs: options.maxVerificationAgeMs,
    });
  }

  solve(problem: PlannerInput): PlannerResult {
    const base = this.planner.solve(problem);
    if (base.reasonCode === "no_options" || base.verb !== "wait") return base;

    const { active, graph } = activeAndGraph(problem);
    const now = new Date(problem.at);
    const found = new Map<string, CommitmentBlock>();
    for (const option of problem.options ?? []) {
      for (const blocker of optionBlockers(
        option,
        active,
        graph,
        this.planner.requireVerified,
        now,
        this.planner.maxVerificationAgeMs,
      )) {
        found.set(
          `${blocker.owner}\u0000${blocker.ledger ?? ""}\u0000${blocker.id}`,
          blocker,
        );
      }
    }
    if (!found.size) return base;

    const refs = [...found.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([, value]) => value);
    const verb = this.mode === "ask" ? "ask" : "verify";
    const intent: Intent = {
      capability: "verify_commitment",
      args: { refs },
    };
    return {
      verb,
      confidence: 0.8,
      reasonCode: "commitment_resolution",
      rationale: `resolve ${refs.length} blocked commitment ${
        refs.length === 1 ? "dependency" : "dependencies"
      }`,
      actionId: "resolve-commitments",
      intent,
      requiresApproval: verb === "ask",
      reversible: true,
      attributes: {
        verification_refs: refs,
        blocked_by: refs,
        base_reason_code: base.reasonCode,
      },
    };
  }
}
