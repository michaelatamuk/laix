import type { Planner, PlannerInput, PlannerResult } from "../../contract/planner.ts";

function previousAction(problem: PlannerInput): string | null {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const raw = attributes.previous_decision ?? attributes.previous;
  if (raw && typeof raw === "object") {
    const value =
      (raw as Record<string, unknown>).action_id ??
      (raw as Record<string, unknown>).actionId;
    if (value !== undefined && value !== null) return String(value);
  }
  const direct = attributes.previous_action_id;
  return direct === undefined || direct === null ? null : String(direct);
}

export class RevalidationPlanner {
  readonly name = "revalidation.v1";
  readonly planner: Planner;
  readonly escalateOnInfeasible: boolean;

  constructor(planner: Planner, options: { escalateOnInfeasible?: boolean } = {}) {
    this.planner = planner;
    this.escalateOnInfeasible = options.escalateOnInfeasible ?? true;
  }

  solve(problem: PlannerInput): PlannerResult {
    const previous = previousAction(problem);
    const current = this.planner.solve(problem);
    if (previous === null) {
      return {
        ...current,
        reasonCode: "revalidated_new",
        attributes: {
          ...(current.attributes ?? {}),
          previous_action_id: null,
          current_action_id: current.actionId ?? null,
        },
      };
    }
    if (current.actionId === previous) {
      return {
        verb: "wait",
        confidence: current.confidence,
        reasonCode: "decision_held",
        rationale: `${previous} is still the best action`,
        actionId: previous,
        score: current.score,
        attributes: {
          ...(current.attributes ?? {}),
          previous_action_id: previous,
          current_action_id: current.actionId ?? null,
          held: true,
        },
      };
    }
    if (
      this.escalateOnInfeasible &&
      (current.reasonCode === "no_feasible_option" || current.reasonCode === "no_options")
    ) {
      return {
        verb: "escalate",
        confidence: 1,
        reasonCode: "decision_escalated",
        rationale: `${previous} is no longer feasible`,
        actionId: previous,
        attributes: {
          ...(current.attributes ?? {}),
          previous_action_id: previous,
          current_action_id: current.actionId ?? null,
          escalated: true,
        },
      };
    }
    return {
      ...current,
      reasonCode: "decision_revised",
      attributes: {
        ...(current.attributes ?? {}),
        previous_action_id: previous,
        current_action_id: current.actionId ?? null,
      },
    };
  }
}
