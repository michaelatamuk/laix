import type { Planner, PlannerInput, PlannerResult } from "../../../contract/planner.ts";
import { commitmentEffect } from "../commitment/commitment-planner.ts";

function defaultSelector(problem: PlannerInput): string {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const hint = attributes.planner;
  if (typeof hint === "string") return hint;
  const options = problem.options ?? [];
  if (
    attributes.commitments ||
    attributes.commitment_ledger ||
    attributes.commitment_graph ||
    attributes.external_commitments ||
    options.some((option) => {
      const effect = commitmentEffect(option);
      return (
        effect.fulfills.length > 0 ||
        effect.violates.length > 0 ||
        effect.creates.length > 0
      );
    })
  ) {
    return "commitment";
  }
  if (
    attributes.requires_approval ||
    options.some(
      (option) =>
        option.requiresApproval || option.destructive || (option.risk ?? 0) >= 0.5,
    )
  ) {
    return "execution";
  }
  if (
    attributes.human_attention_budget ||
    attributes.attention_budget ||
    attributes.approval
  ) {
    return "human_attention";
  }
  if (attributes.mdp_model) return "mdp";
  if (attributes.pomdp_model) return "pomdp";
  return "utility";
}

export class PortfolioPlanner {
  readonly name = "portfolio.v1";
  readonly planners: Record<string, Planner>;
  readonly default: string;
  private readonly selector: (problem: PlannerInput) => string;

  constructor(
    planners: Record<string, Planner>,
    options: {
      selector?: (problem: PlannerInput) => string;
      default?: string;
    } = {},
  ) {
    const names = Object.keys(planners);
    if (!names.length) throw new Error("a portfolio needs at least one planner");
    this.planners = { ...planners };
    this.selector = options.selector ?? defaultSelector;
    this.default = options.default ?? names[0]!;
    if (!this.planners[this.default]) {
      throw new Error(`unknown default planner: ${this.default}`);
    }
  }

  solve(problem: PlannerInput): PlannerResult {
    let selected = this.selector(problem);
    if (!this.planners[selected]) selected = this.default;
    const result = this.planners[selected]!.solve(problem);
    return {
      ...result,
      attributes: {
        ...(result.attributes ?? {}),
        planner: selected,
        portfolio: Object.keys(this.planners).sort(),
      },
    };
  }
}
