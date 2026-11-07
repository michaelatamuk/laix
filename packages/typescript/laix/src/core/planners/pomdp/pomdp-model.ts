import type {
  ObservationProbability,
  PomdpModelOptions,
  PomdpTransition,
} from "./pomdp-planner.ts";

export class PomdpModel {
  readonly states: string[];
  readonly actions: string[];
  readonly observations: string[];
  readonly transitions: Required<PomdpTransition>[];
  readonly observationTable: Required<ObservationProbability>[];
  readonly discount: number;
  readonly horizon: number;

  constructor(options: PomdpModelOptions) {
    if (!options.states.length) throw new Error("a POMDP needs at least one state");
    if (!options.actions.length) throw new Error("a POMDP needs at least one action");
    if (!options.observations.length) throw new Error("a POMDP needs at least one observation");
    if (new Set(options.states).size !== options.states.length) throw new Error("POMDP states must be unique");
    if (new Set(options.actions).size !== options.actions.length) throw new Error("POMDP actions must be unique");
    if (new Set(options.observations).size !== options.observations.length) throw new Error("POMDP observations must be unique");
    this.states = [...options.states];
    this.actions = [...options.actions];
    this.observations = [...options.observations];
    this.discount = options.discount ?? 0.9;
    this.horizon = options.horizon ?? 3;
    if (this.discount < 0 || this.discount > 1) throw new Error("discount must be between zero and one");
    if (this.horizon < 0) throw new Error("horizon must not be negative");

    this.transitions = options.transitions.map((item) => ({
      state: item.state,
      action: item.action,
      nextState: item.nextState,
      probability: item.probability ?? 1,
      reward: item.reward ?? 0,
    }));
    this.observationTable = options.observationTable.map((item) => ({
      nextState: item.nextState,
      action: item.action,
      observation: item.observation,
      probability: item.probability ?? 1,
    }));

    for (const item of this.transitions) {
      if (!this.states.includes(item.state) || !this.states.includes(item.nextState)) {
        throw new Error(`transition refers to an unknown state: ${JSON.stringify(item)}`);
      }
      if (!this.actions.includes(item.action)) {
        throw new Error(`transition refers to an unknown action: ${JSON.stringify(item)}`);
      }
      if (item.probability < 0 || item.probability > 1) {
        throw new Error("transition probability must be between zero and one");
      }
    }
    for (const item of this.observationTable) {
      if (!this.states.includes(item.nextState)) {
        throw new Error(`observation refers to an unknown state: ${JSON.stringify(item)}`);
      }
      if (!this.actions.includes(item.action)) {
        throw new Error(`observation refers to an unknown action: ${JSON.stringify(item)}`);
      }
      if (!this.observations.includes(item.observation)) {
        throw new Error(`unknown observation: ${JSON.stringify(item)}`);
      }
      if (item.probability < 0 || item.probability > 1) {
        throw new Error("observation probability must be between zero and one");
      }
    }

    for (const state of this.states) {
      for (const action of this.actions) {
        const rows = this.transitionRows(state, action);
        if (rows.length) {
          const total = rows.reduce((sum, item) => sum + item.probability, 0);
          if (Math.abs(total - 1) > 1e-6) {
            throw new Error(`transitions for ${state}/${action} sum to ${total.toFixed(6)}`);
          }
        }
      }
    }

    const reachable = new Set(
      this.transitions
        .filter((item) => item.probability > 0)
        .map((item) => `${item.nextState}\u0000${item.action}`),
    );
    for (const key of [...reachable].sort()) {
      const [nextState, action] = key.split("\u0000") as [string, string];
      const rows = this.observationRows(nextState, action);
      if (!rows.length) {
        throw new Error(`missing observations for ${nextState}/${action}`);
      }
      const total = rows.reduce((sum, item) => sum + item.probability, 0);
      if (Math.abs(total - 1) > 1e-6) {
        throw new Error(`observations for ${nextState}/${action} sum to ${total.toFixed(6)}`);
      }
    }
  }

  transitionRows(state: string, action: string): Required<PomdpTransition>[] {
    return this.transitions.filter(
      (item) => item.state === state && item.action === action,
    );
  }

  observationRows(nextState: string, action: string): Required<ObservationProbability>[] {
    return this.observationTable.filter(
      (item) => item.nextState === nextState && item.action === action,
    );
  }

  actionAvailable(state: string, action: string): boolean {
    return this.transitionRows(state, action).length > 0;
  }
}
