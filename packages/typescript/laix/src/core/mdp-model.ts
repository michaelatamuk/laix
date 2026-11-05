import type { MdpModelOptions, MdpTransition } from "./mdp.ts";

export class MdpModel {
  readonly states: string[];
  readonly actions: string[];
  readonly transitions: Required<MdpTransition>[];
  readonly start: string;
  readonly discount: number;
  readonly horizon: number | null;

  constructor(options: MdpModelOptions) {
    if (!options.states.length) throw new Error("an MDP needs at least one state");
    if (new Set(options.states).size !== options.states.length) {
      throw new Error("MDP states must be unique");
    }
    if (new Set(options.actions).size !== options.actions.length) {
      throw new Error("MDP actions must be unique");
    }
    if (!options.states.includes(options.start)) {
      throw new Error(`unknown start state: ${options.start}`);
    }
    this.states = [...options.states];
    this.actions = [...options.actions];
    this.start = options.start;
    this.discount = options.discount ?? 0.9;
    this.horizon = options.horizon === undefined ? 20 : options.horizon;
    if (this.discount < 0 || this.discount > 1) {
      throw new Error("discount must be between zero and one");
    }
    if (this.horizon !== null && this.horizon < 0) {
      throw new Error("horizon must not be negative");
    }
    this.transitions = options.transitions.map((item) => ({
      state: item.state,
      action: item.action,
      nextState: item.nextState,
      probability: item.probability ?? 1,
      reward: item.reward ?? 0,
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
    for (const state of this.states) {
      for (const action of this.actions) {
        const rows = this.outgoing(state, action);
        if (rows.length) {
          const total = rows.reduce((sum, item) => sum + item.probability, 0);
          if (Math.abs(total - 1) > 1e-6) {
            throw new Error(`transitions for ${state}/${action} sum to ${total.toFixed(6)}`);
          }
        }
      }
    }
  }

  outgoing(state: string, action: string): Required<MdpTransition>[] {
    return this.transitions.filter(
      (item) => item.state === state && item.action === action,
    );
  }

  actionsFor(state: string): string[] {
    return this.actions.filter((action) => this.outgoing(state, action).length > 0);
  }
}
