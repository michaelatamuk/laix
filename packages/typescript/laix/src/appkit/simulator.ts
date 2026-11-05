import type { DecisionEngine, DecisionProblem } from "../core/engine.ts";
import type { MdpModel } from "../core/mdp.ts";
import { SimulationReport } from "./simulation-report.ts";

export { SimulationReport };

export type Step = (state: string, action: string) => [string, number];
export type RandomStep = (
  state: string,
  action: string,
  rng: () => number,
) => [string, number];

function seededRandom(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value = (value + 0x6d2b79f5) >>> 0;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface SimulationStep {
  step: number;
  state: string;
  action: string | null;
  reward: number;
  nextState: string;
}

export interface SimulationResult {
  scenario: string;
  steps: SimulationStep[];
  totalReward: number;
  finalState: string;
}

export interface SimulatorOptions {
  start: string;
  horizon?: number;
  name?: string;
  seed?: number;
  randomStep?: RandomStep;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class Simulator {
  readonly step: Step;
  readonly actions: string[];
  readonly start: string;
  readonly horizon: number;
  readonly name: string;
  readonly seed: number | undefined;
  readonly randomStep: RandomStep | undefined;

  constructor(step: Step, actions: string[], options: SimulatorOptions) {
    if (!actions.length) throw new Error("a simulator needs at least one action");
    const horizon = options.horizon ?? 10;
    if (horizon < 0) throw new Error("horizon must not be negative");
    this.step = step;
    this.actions = [...actions];
    this.start = options.start;
    this.horizon = horizon;
    this.name = options.name ?? "scenario";
    this.seed = options.seed;
    this.randomStep = options.randomStep;
  }

  run(engine: DecisionEngine): SimulationResult {
    let state = this.start;
    const steps: SimulationStep[] = [];
    let total = 0;
    const rng =
      this.randomStep !== undefined && this.seed !== undefined
        ? seededRandom(this.seed)
        : undefined;
    for (let index = 0; index < this.horizon; index += 1) {
      const problem: DecisionProblem = {
        subject: this.name,
        at: new Date().toISOString(),
        options: [],
        attributes: { state },
      };
      const plan = engine.solve(problem);
      const action = plan.actionId ?? null;
      if (action === null || !this.actions.includes(action)) {
        steps.push({ step: index, state, action, reward: 0, nextState: state });
        break;
      }
      const [nextState, reward] =
        this.randomStep !== undefined && rng !== undefined
          ? this.randomStep(state, action, rng)
          : this.step(state, action);
      steps.push({ step: index, state, action, reward, nextState });
      total += reward;
      state = nextState;
    }
    return {
      scenario: this.name,
      steps,
      totalReward: round(total),
      finalState: state,
    };
  }

  static fromMdp(
    model: MdpModel,
    options: { start?: string; seed?: number } = {},
  ): Simulator {
    const resolvedStart = options.start ?? model.start;
    const horizon = model.horizon ?? 10;
    const step: Step = (state, action) => {
      const rows = model.outgoing(state, action);
      if (!rows.length) return [state, 0];
      const chosen = [...rows].sort((left, right) =>
        right.probability !== left.probability
          ? right.probability - left.probability
          : left.nextState < right.nextState
            ? -1
            : 1,
      )[0]!;
      return [chosen.nextState, chosen.reward];
    };
    const randomStep: RandomStep = (state, action, rng) => {
      const rows = model.outgoing(state, action);
      if (!rows.length) return [state, 0];
      const roll = rng();
      let cumulative = 0;
      for (const item of rows) {
        cumulative += item.probability;
        if (roll <= cumulative) return [item.nextState, item.reward];
      }
      const last = rows[rows.length - 1]!;
      return [last.nextState, last.reward];
    };
    return new Simulator(step, model.actions, {
      start: resolvedStart,
      horizon,
      name: `mdp:${model.start}`,
      seed: options.seed,
      randomStep: options.seed === undefined ? undefined : randomStep,
    });
  }
}

export interface Scenario {
  name: string;
  simulator: Simulator;
  optimum?: number | null;
}

export interface EngineScore {
  engine: string;
  scenario: string;
  totalReward: number;
  steps: number;
  optimalityGap: number | null;
}

export function compareEngines(
  engines: Record<string, DecisionEngine>,
  scenarios: Scenario[],
): SimulationReport {
  const rows: EngineScore[] = [];
  for (const scenario of scenarios) {
    for (const [name, engine] of Object.entries(engines)) {
      const result = scenario.simulator.run(engine);
      const optimum = scenario.optimum ?? null;
      const gap =
        optimum === null
          ? null
          : round(
              Math.max(
                0,
                (optimum - result.totalReward) / Math.max(Math.abs(optimum), 1e-9),
              ),
            );
      rows.push({
        engine: name,
        scenario: scenario.name,
        totalReward: result.totalReward,
        steps: result.steps.length,
        optimalityGap: gap,
      });
    }
  }
  return new SimulationReport(rows);
}

function rng(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value = (value + 0x6d2b79f5) >>> 0;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function seededScenarios(
  seed: number,
  options: { count?: number; horizon?: number; actions?: string[] } = {},
): Scenario[] {
  const count = options.count ?? 3;
  const horizon = options.horizon ?? 8;
  const actions = options.actions ?? ["a", "b"];
  if (count < 1) throw new Error("count must be at least one");
  if (horizon < 1) throw new Error("horizon must be at least one");
  const random = rng(seed);
  const scenarios: Scenario[] = [];
  for (let index = 0; index < count; index += 1) {
    const table = new Map<string, Record<string, number>>();
    for (let stepIndex = 0; stepIndex < horizon; stepIndex += 1) {
      table.set(
        `s${stepIndex}`,
        Object.fromEntries(
          actions.map((action) => [action, round(random() * 2 - 1)]),
        ),
      );
    }
    const step: Step = (state, action) => {
      const value = table.get(state)?.[action] ?? 0;
      const current = state.startsWith("s") ? Number(state.slice(1)) : 0;
      return [`s${current + 1}`, value];
    };
    const simulator = new Simulator(step, actions, {
      start: "s0",
      horizon,
      name: `seeded-${seed}-${index}`,
    });
    let optimum = 0;
    for (let stepIndex = 0; stepIndex < horizon; stepIndex += 1) {
      const values = Object.values(table.get(`s${stepIndex}`) ?? {});
      optimum += values.length ? Math.max(...values) : 0;
    }
    scenarios.push({
      name: `seeded-${seed}-${index}`,
      simulator,
      optimum: round(optimum),
    });
  }
  return scenarios;
}
