import type { Planner, PlannerInput, PlannerResult } from "../../../contract/planner.ts";

function conflictId(conflict: Record<string, unknown>): string {
  return String(conflict.id ?? `${conflict.left}:${conflict.right}`);
}

export class ConflictResolutionPlanner {
  readonly name = "conflict_resolution.v1";
  readonly planner: Planner | null;
  readonly severityLimit: number;
  readonly escalateAt: number;

  constructor(
    planner?: Planner,
    options: { severityLimit?: number; escalateAt?: number } = {},
  ) {
    this.planner = planner ?? null;
    this.severityLimit = options.severityLimit ?? 0.5;
    this.escalateAt = options.escalateAt ?? 0.8;
    if (this.severityLimit < 0 || this.severityLimit > 1) {
      throw new Error("severityLimit must be between zero and one");
    }
    if (this.escalateAt < 0 || this.escalateAt > 1) {
      throw new Error("escalateAt must be between zero and one");
    }
  }

  solve(problem: PlannerInput): PlannerResult {
    const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
    const raw = attributes.goal_conflicts;
    const conflicts = (Array.isArray(raw) ? raw : [])
      .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
      .filter((item) => Number(item.severity ?? 0) >= this.severityLimit);
    if (!conflicts.length) {
      if (this.planner) return this.planner.solve(problem);
      return {
        verb: "wait",
        confidence: 1,
        reasonCode: "no_goal_conflict",
        rationale: "no goal conflict needs resolution",
        score: 0,
      };
    }

    const wanted = new Set(conflicts.map(conflictId));
    for (const option of problem.options ?? []) {
      const params = (option.params ?? {}) as Record<string, unknown>;
      const resolves = new Set(
        (Array.isArray(params.resolves) ? params.resolves : []).map(String),
      );
      if ([...wanted].every((item) => resolves.has(item))) {
        return {
          verb: option.verb,
          confidence: 0.8,
          reasonCode: "goal_conflict_resolved",
          rationale: `${option.id} resolves the active goal conflicts`,
          actionId: option.id,
          attributes: { goal_conflicts: conflicts },
        };
      }
    }

    const escalate = conflicts.some(
      (item) => Number(item.severity ?? 0) >= this.escalateAt,
    );
    return {
      verb: escalate ? "escalate" : "ask",
      confidence: 0.8,
      reasonCode: escalate ? "goal_conflict" : "goal_conflict_needs_choice",
      rationale: `${conflicts.length} goal conflicts need a decision`,
      attributes: { goal_conflicts: conflicts },
    };
  }
}
