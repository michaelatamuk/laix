import type { Planner, PlannerInput, PlannerResult } from "../../contract/planner.ts";

export interface PastDecision {
  subject: string;
  actionId: string;
  verb?: "act" | "wait" | "ask" | "observe" | "guide" | "verify" | "escalate";
  attributes?: Record<string, unknown>;
}

function tokens(value: string): Set<string> {
  return new Set(value.toLowerCase().match(/[a-z0-9]+/g) ?? []);
}

function similarity(problem: PlannerInput, past: PastDecision): number {
  const wanted = tokens(problem.subject);
  const found = tokens(past.subject);
  let token = 0;
  if (wanted.size && found.size) {
    let shared = 0;
    for (const item of wanted) if (found.has(item)) shared += 1;
    token = shared / new Set([...wanted, ...found]).size;
  }
  const action = (problem.options ?? []).some((option) => option.id === past.actionId)
    ? 1
    : 0;
  return Math.round((0.7 * token + 0.3 * action) * 1e6) / 1e6;
}

export class CaseBasedPlanner {
  readonly name = "case_based.v1";
  readonly cases: PastDecision[];
  readonly fallback: Planner | null;
  readonly threshold: number;

  constructor(
    cases: PastDecision[],
    options: { fallback?: Planner; threshold?: number } = {},
  ) {
    this.threshold = options.threshold ?? 0.2;
    if (this.threshold < 0 || this.threshold > 1) {
      throw new Error("threshold must be between zero and one");
    }
    this.cases = [...cases];
    this.fallback = options.fallback ?? null;
  }

  solve(problem: PlannerInput): PlannerResult {
    const scored = this.cases
      .map((past) => ({ similarity: similarity(problem, past), past }))
      .sort((left, right) =>
        right.similarity !== left.similarity
          ? right.similarity - left.similarity
          : left.past.subject < right.past.subject
            ? -1
            : left.past.subject > right.past.subject
              ? 1
              : left.past.actionId < right.past.actionId
                ? -1
                : 1,
      );
    const best = scored[0];
    if (best && best.similarity >= this.threshold) {
      return {
        verb: best.past.verb ?? "act",
        confidence: best.similarity,
        reasonCode: "case_based",
        rationale: `${best.past.subject} is the closest past decision`,
        actionId: best.past.actionId,
        attributes: {
          case_subject: best.past.subject,
          case_similarity: best.similarity,
          ...(best.past.attributes ?? {}),
        },
      };
    }
    if (this.fallback) return this.fallback.solve(problem);
    return {
      verb: "wait",
      confidence: 1,
      reasonCode: "no_case",
      rationale: "no similar past decision",
      score: 0,
    };
  }
}
