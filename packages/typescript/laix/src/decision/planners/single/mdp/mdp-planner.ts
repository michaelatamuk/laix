import type { PlannerInput, PlannerResult } from "../../../contract/planner.ts";
import { MdpModel } from "./mdp-model.ts";

export { MdpModel };

export interface MdpTransition {
  state: string;
  action: string;
  nextState: string;
  probability?: number;
  reward?: number;
}

export interface MdpModelOptions {
  states: string[];
  actions: string[];
  transitions: MdpTransition[];
  start: string;
  discount?: number;
  horizon?: number | null;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function qValue(
  model: MdpModel,
  state: string,
  action: string,
  values: Record<string, number>,
): number {
  return model
    .outgoing(state, action)
    .reduce(
      (total, item) =>
        total + item.probability * (item.reward + model.discount * values[item.nextState]!),
      0,
    );
}

export function valueIteration(
  model: MdpModel,
  options: { horizon?: number | null; tolerance?: number; maxIterations?: number } = {},
): Record<string, number> {
  let values: Record<string, number> = Object.fromEntries(
    model.states.map((state) => [state, 0]),
  );
  const limit = options.horizon === undefined ? model.horizon : options.horizon;
  if (limit !== null && limit <= 0) return values;
  const iterations = limit ?? options.maxIterations ?? 1000;
  const tolerance = options.tolerance ?? 1e-9;
  for (let index = 0; index < iterations; index += 1) {
    const updated: Record<string, number> = {};
    let delta = 0;
    for (const state of model.states) {
      const actions = model.actionsFor(state);
      if (!actions.length) {
        updated[state] = 0;
        continue;
      }
      const value = Math.max(...actions.map((action) => qValue(model, state, action, values)));
      updated[state] = value;
      delta = Math.max(delta, Math.abs(value - values[state]!));
    }
    values = updated;
    if (delta <= tolerance) break;
  }
  return values;
}

function lookaheadValues(model: MdpModel): Record<string, number> {
  if (model.horizon === null) return valueIteration(model);
  return valueIteration(model, { horizon: Math.max(-1, model.horizon - 1) });
}

export function actionValues(
  model: MdpModel,
  state: string,
  values?: Record<string, number>,
): Array<[string, number]> {
  const resolved = values ?? lookaheadValues(model);
  return model
    .actionsFor(state)
    .map((action): [string, number] => [
      action,
      round(qValue(model, state, action, resolved)),
    ])
    .sort((left, right) =>
      right[1] !== left[1] ? right[1] - left[1] : left[0] < right[0] ? -1 : 1,
    );
}

export class MDPPlanner {
  readonly name = "mdp.v1";
  readonly model: MdpModel;
  readonly state: string;

  constructor(model: MdpModel, options: { state?: string } = {}) {
    this.model = model;
    this.state = options.state ?? model.start;
  }

  solve(problem: PlannerInput): PlannerResult {
    const state = String(problem.attributes?.state ?? this.state);
    if (!this.model.states.includes(state)) throw new Error(`unknown state: ${state}`);
    const rows = actionValues(this.model, state);
    if (!rows.length) {
      return {
        verb: "wait",
        confidence: 1.0,
        reasonCode: "terminal_state",
        rationale: `${state} has no action to take`,
        score: 0.0,
        attributes: { state },
      };
    }

    const [bestAction, bestValue] = rows[0]!;
    const second = rows[1]?.[1];
    return {
      verb: "act",
      confidence: this.confidence(bestValue, second),
      reasonCode: "mdp_plan",
      rationale: `${bestAction} has the highest expected value ${bestValue.toFixed(3)} from ${state}`,
      actionId: bestAction,
      score: bestValue,
      alternatives: rows.slice(1).map(([action, value]) => ({
        action_id: action,
        value,
        rejected_because: "lower expected value",
      })),
      attributes: {
        state,
        expected_value: bestValue,
        discount: this.model.discount,
        horizon: this.model.horizon,
      },
    };
  }

  private confidence(best: number, second: number | undefined): number {
    if (second === undefined) return 1.0;
    const gap = Math.max(0, best - second);
    return Math.min(1, Math.max(0, 0.5 + 0.5 * (gap / Math.max(Math.abs(best), 1e-9))));
  }
}

export function planActions(model: MdpModel, state?: string): string[] {
  let current = state ?? model.start;
  const path: string[] = [];
  const seen = new Set<string>();
  while (!seen.has(current)) {
    seen.add(current);
    const rows = actionValues(model, current);
    if (!rows.length) break;
    const action = rows[0]![0];
    path.push(`${current}:${action}`);
    const outcomes = model.outgoing(current, action);
    if (!outcomes.length) break;
    current = [...outcomes].sort((left, right) =>
      right.probability !== left.probability
        ? right.probability - left.probability
        : left.nextState < right.nextState
          ? -1
          : 1,
    )[0]!.nextState;
  }
  return path;
}
