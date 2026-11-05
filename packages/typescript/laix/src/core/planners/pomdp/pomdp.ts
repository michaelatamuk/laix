import type { DecisionProblem, Plan } from "../../engine.ts";
import { MdpModel, valueIteration } from "../mdp/mdp.ts";
import { clamp } from "../../contracts.ts";
import { PomdpModel } from "./pomdp-model.ts";

export { PomdpModel };

export interface PomdpTransition {
  state: string;
  action: string;
  nextState: string;
  probability?: number;
  reward?: number;
}

export interface ObservationProbability {
  nextState: string;
  action: string;
  observation: string;
  probability?: number;
}

export interface PomdpModelOptions {
  states: string[];
  actions: string[];
  observations: string[];
  transitions: PomdpTransition[];
  observationTable: ObservationProbability[];
  discount?: number;
  horizon?: number;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export type BeliefState = Record<string, number>;

export function normalizeBelief(belief: BeliefState, states: string[]): BeliefState {
  const allowed = new Set(states);
  const clean: BeliefState = {};
  for (const [state, probability] of Object.entries(belief)) {
    if (allowed.has(state)) clean[state] = Math.max(0, Number(probability));
  }
  const total = Object.values(clean).reduce((sum, value) => sum + value, 0);
  if (total <= 0) {
    const size = Math.max(1, states.length);
    return Object.fromEntries(states.map((state) => [state, 1 / size]));
  }
  return Object.fromEntries(
    Object.entries(clean).map(([state, probability]) => [
      state,
      round(probability / total),
    ]),
  );
}

export function beliefFromState(state: string, states: string[]): BeliefState {
  if (!states.includes(state)) throw new Error(`unknown state: ${state}`);
  return Object.fromEntries(states.map((item) => [item, item === state ? 1 : 0]));
}

export function beliefUpdate(
  model: PomdpModel,
  belief: BeliefState,
  action: string,
  observation: string,
): BeliefState {
  const current = normalizeBelief(belief, model.states);
  const predicted: BeliefState = {};
  for (const nextState of model.states) {
    let probability = 0;
    for (const state of model.states) {
      for (const item of model.transitionRows(state, action)) {
        if (item.nextState === nextState) {
          probability += (current[state] ?? 0) * item.probability;
        }
      }
    }
    if (probability) predicted[nextState] = probability;
  }
  if (!Object.keys(predicted).length) return { ...current };

  const unnormalised: BeliefState = {};
  for (const nextState of Object.keys(predicted)) {
    const likelihood = model
      .observationRows(nextState, action)
      .find((item) => item.observation === observation)?.probability ?? 0;
    unnormalised[nextState] = predicted[nextState]! * likelihood;
  }
  const total = Object.values(unnormalised).reduce((sum, value) => sum + value, 0);
  if (total <= 0) return normalizeBelief(predicted, model.states);
  return Object.fromEntries(
    Object.entries(unnormalised).map(([state, probability]) => [
      state,
      round(probability / total),
    ]),
  );
}

export function observationProbability(
  model: PomdpModel,
  belief: BeliefState,
  action: string,
  observation: string,
): number {
  const current = normalizeBelief(belief, model.states);
  let total = 0;
  for (const nextState of model.states) {
    let transition = 0;
    for (const state of model.states) {
      for (const item of model.transitionRows(state, action)) {
        if (item.nextState === nextState) {
          transition += (current[state] ?? 0) * item.probability;
        }
      }
    }
    const chance =
      model
        .observationRows(nextState, action)
        .find((item) => item.observation === observation)?.probability ?? 0;
    total += transition * chance;
  }
  return total;
}

export function beliefEntropy(belief: BeliefState): number {
  const total = Object.values(belief).reduce((sum, value) => sum + value, 0);
  if (total <= 0) return 0;
  let entropy = 0;
  for (const probability of Object.values(belief)) {
    const value = probability / total;
    if (value > 0) entropy -= value * Math.log2(value);
  }
  return round(entropy);
}

function immediateReward(model: PomdpModel, belief: BeliefState, action: string): number {
  let total = 0;
  for (const state of model.states) {
    for (const item of model.transitionRows(state, action)) {
      total += (belief[state] ?? 0) * item.probability * item.reward;
    }
  }
  return total;
}

function bestValue(
  model: PomdpModel,
  belief: BeliefState,
  depth: number,
  cache: Map<string, number>,
): number {
  if (depth < 0) return 0;
  const key = `${depth}|${Object.entries(belief).sort().map(([state, value]) => `${state}:${value}`).join(",")}`;
  const cached = cache.get(key);
  if (cached !== undefined) return cached;
  const actions = model.actions.filter((action) =>
    Object.keys(belief).some((state) => model.actionAvailable(state, action)),
  );
  if (!actions.length) {
    cache.set(key, 0);
    return 0;
  }
  let best = Number.NEGATIVE_INFINITY;
  for (const action of actions) {
    let value = immediateReward(model, belief, action);
    if (depth > 0) {
      let future = 0;
      for (const observation of model.observations) {
        const chance = observationProbability(model, belief, action, observation);
        if (chance <= 0) continue;
        future += chance * bestValue(
          model,
          beliefUpdate(model, belief, action, observation),
          depth - 1,
          cache,
        );
      }
      value += model.discount * future;
    }
    best = Math.max(best, value);
  }
  cache.set(key, best);
  return best;
}

export function pomdpValue(
  model: PomdpModel,
  belief: BeliefState,
  options: { horizon?: number } = {},
): number {
  const resolved = normalizeBelief(belief, model.states);
  const steps = options.horizon ?? model.horizon;
  if (steps <= 0) return 0;
  return round(bestValue(model, resolved, steps - 1, new Map()));
}

export interface PlannerComparison {
  pomdp: number;
  mdp: number;
  gap: number;
  state: string;
}

export function comparePomdpToMdp(
  pomdp: PomdpModel,
  mdp: MdpModel,
  belief: BeliefState,
  options: { horizon?: number } = {},
): PlannerComparison {
  const resolved = normalizeBelief(belief, pomdp.states);
  const state = Object.entries(resolved).sort((left, right) =>
    right[1] !== left[1] ? right[1] - left[1] : left[0] < right[0] ? -1 : 1,
  )[0]![0];
  const pomdpScore = pomdpValue(pomdp, resolved, options);
  const mdpScore = round(valueIteration(mdp)[state]!);
  return {
    pomdp: pomdpScore,
    mdp: mdpScore,
    gap: round(Math.abs(pomdpScore - mdpScore)),
    state,
  };
}

export class POMDPEngine {
  readonly name = "pomdp.v1";
  readonly model: PomdpModel;
  readonly belief: BeliefState;

  constructor(model: PomdpModel, options: { belief?: BeliefState } = {}) {
    this.model = model;
    this.belief = { ...(options.belief ?? {}) };
  }

  solve(problem: DecisionProblem): Plan {
    const belief = this.resolveBelief(problem.attributes ?? {});
    const horizon = Number(problem.attributes?.horizon ?? this.model.horizon);
    const depth = Math.max(-1, horizon - 1);
    const cache = new Map<string, number>();
    const rows = this.model.actions
      .filter((action) =>
        Object.keys(belief).some((state) => this.model.actionAvailable(state, action)),
      )
      .map((action): [string, number] => {
        let value = immediateReward(this.model, belief, action);
        if (depth > 0) {
          let future = 0;
          for (const observation of this.model.observations) {
            const chance = observationProbability(this.model, belief, action, observation);
            if (chance <= 0) continue;
            future += chance * bestValue(
              this.model,
              beliefUpdate(this.model, belief, action, observation),
              depth - 1,
              cache,
            );
          }
          value += this.model.discount * future;
        }
        return [action, round(value)];
      })
      .sort((left, right) =>
        right[1] !== left[1] ? right[1] - left[1] : left[0] < right[0] ? -1 : 1,
      );
    if (!rows.length) {
      return {
        verb: "wait",
        confidence: 1,
        reasonCode: "no_action",
        rationale: "no action is available under the current belief",
        score: 0,
      };
    }
    const [bestAction, bestValueScore] = rows[0]!;
    const second = rows[1]?.[1];
    const confidence =
      second === undefined
        ? 1
        : clamp(0.5 + 0.5 * (Math.max(0, bestValueScore - second) / Math.max(Math.abs(bestValueScore), 1e-9)));
    return {
      verb: "act",
      confidence,
      reasonCode: "pomdp_plan",
      rationale: `${bestAction} has the highest expected value ${bestValueScore.toFixed(3)} under the current belief`,
      actionId: bestAction,
      score: bestValueScore,
      alternatives: rows.slice(1).map(([action, value]) => ({
        action_id: action,
        value,
        rejected_because: "lower expected value",
      })),
      attributes: {
        belief,
        entropy: beliefEntropy(belief),
        horizon,
      },
    };
  }

  private resolveBelief(attributes: Record<string, unknown>): BeliefState {
    if (attributes.belief && typeof attributes.belief === "object") {
      return normalizeBelief(attributes.belief as BeliefState, this.model.states);
    }
    if (Object.keys(this.belief).length) {
      return normalizeBelief(this.belief, this.model.states);
    }
    const state = attributes.state;
    if (typeof state === "string" && state) {
      return beliefFromState(state, this.model.states);
    }
    const size = this.model.states.length;
    return Object.fromEntries(this.model.states.map((item) => [item, 1 / size]));
  }
}
