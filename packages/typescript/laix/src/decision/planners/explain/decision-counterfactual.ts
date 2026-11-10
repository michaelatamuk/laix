import type { Planner, PlannerInput } from "../../contract/planner.ts";
import { CommitmentGraph, commitmentRef } from "../../domain/commitments/commitments.ts";
import { normalizeCommitment } from "../../domain/commitments/commitment.ts";

export interface CounterfactualOutcome {
  name: string;
  base_action_id: string | null;
  counterfactual_action_id: string | null;
  changed: boolean;
}

export interface DecisionCounterfactualResult {
  base_action_id: string | null;
  outcomes: CounterfactualOutcome[];
  flips: CounterfactualOutcome[];
}

export function decisionCounterfactual(
  problem: PlannerInput,
  planner: Planner,
  candidates: Record<string, PlannerInput>,
): DecisionCounterfactualResult {
  const base = planner.solve(problem);
  const outcomes = Object.entries(candidates).map(([name, candidate]) => {
    const result = planner.solve(candidate);
    return {
      name,
      base_action_id: base.actionId ?? null,
      counterfactual_action_id: result.actionId ?? null,
      changed: result.actionId !== base.actionId,
    };
  });
  return {
    base_action_id: base.actionId ?? null,
    outcomes,
    flips: outcomes.filter((item) => item.changed),
  };
}

export function commitmentVerificationCounterfactual(
  problem: PlannerInput,
  planner: Planner,
  options: { now?: Date } = {},
): DecisionCounterfactualResult {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const graph = attributes.commitment_graph;
  if (!(graph instanceof CommitmentGraph)) {
    return decisionCounterfactual(problem, planner, {});
  }
  const timestamp = (options.now ?? new Date(problem.at)).toISOString();
  const candidates: Record<string, PlannerInput> = {};
  for (const item of graph.external) {
    if (item.source !== "reported" && item.source !== "verified") continue;
    if (item.source === "verified" && item.verifiedAt) continue;
    const replacement = normalizeCommitment({
      ...item,
      source: "verified",
      verifiedAt: timestamp,
    });
    const updated = graph.external.map((other) =>
      commitmentRef(other).owner === commitmentRef(item).owner &&
      (commitmentRef(other).ledger ?? null) === (commitmentRef(item).ledger ?? null) &&
      commitmentRef(other).id === commitmentRef(item).id
        ? replacement
        : other,
    );
    const candidateGraph = new CommitmentGraph(graph.local, updated);
    const name = `${item.owner}/${item.id}`;
    candidates[name] = {
      ...problem,
      attributes: { ...attributes, commitment_graph: candidateGraph },
    };
  }
  return decisionCounterfactual(problem, planner, candidates);
}
