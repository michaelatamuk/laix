import { MdpModel, type MdpModelOptions } from "./planners/mdp/mdp.ts";

export type Transition = [string, string, string, number];

export interface LearnedTransition {
  state: string;
  action: string;
  probabilities: Record<string, number>;
  expectedReward: number;
  count: number;
}

interface Snapshot {
  counts: Array<{
    state: string;
    action: string;
    nextState: string;
    count: number;
  }>;
  rewards: Array<{ state: string; action: string; reward: number }>;
  totals: Array<{ state: string; action: string; total: number }>;
}

function pairKey(state: string, action: string): string {
  return `${state}\u0000${action}`;
}

function transitionKey(state: string, action: string, nextState: string): string {
  return `${state}\u0000${action}\u0000${nextState}`;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class ModelLearner {
  readonly prior: number;
  history: Array<[number, boolean]> = [];
  private counts = new Map<string, { state: string; action: string; nextState: string; count: number }>();
  private rewards = new Map<string, number>();
  private totals = new Map<string, number>();
  private bestScoreValue: number | null = null;
  private best: Snapshot | null = null;

  constructor(options: { prior?: number } = {}) {
    this.prior = options.prior ?? 0.5;
    if (this.prior < 0) throw new Error("prior must not be negative");
  }

  get bestScore(): number | null {
    return this.bestScoreValue;
  }

  observe(state: string, action: string, nextState: string, reward: number): void {
    const key = transitionKey(state, action, nextState);
    const item = this.counts.get(key);
    if (item) item.count += 1;
    else this.counts.set(key, { state, action, nextState, count: 1 });
    const pair = pairKey(state, action);
    this.rewards.set(pair, (this.rewards.get(pair) ?? 0) + Number(reward));
    this.totals.set(pair, (this.totals.get(pair) ?? 0) + 1);
  }

  transitionProbabilities(state: string, action: string): Record<string, number> {
    const pair = pairKey(state, action);
    const total = this.totals.get(pair) ?? 0;
    const outcomes = [...this.counts.values()]
      .filter((item) => item.state === state && item.action === action)
      .sort((left, right) => (left.nextState < right.nextState ? -1 : 1));
    const denominator = total + this.prior * Math.max(1, outcomes.length);
    if (denominator <= 0) return {};
    return Object.fromEntries(
      outcomes.map((item) => [
        item.nextState,
        round((item.count + this.prior) / denominator),
      ]),
    );
  }

  expectedReward(state: string, action: string): number {
    const pair = pairKey(state, action);
    const total = this.totals.get(pair) ?? 0;
    return total ? round((this.rewards.get(pair) ?? 0) / total) : 0;
  }

  learned(): LearnedTransition[] {
    return [...this.totals.keys()]
      .sort()
      .map((pair) => {
        const [state, action] = pair.split("\u0000") as [string, string];
        return {
          state,
          action,
          probabilities: this.transitionProbabilities(state, action),
          expectedReward: this.expectedReward(state, action),
          count: this.totals.get(pair) ?? 0,
        };
      });
  }

  evaluate(validation: Transition[]): number {
    if (!validation.length) return 0;
    const scores = validation.map(([state, action, nextState, reward]) => {
      const probability = this.transitionProbabilities(state, action)[nextState] ?? 1e-9;
      const rewardError = Math.abs(this.expectedReward(state, action) - Number(reward));
      return Math.log(probability) - rewardError;
    });
    return round(scores.reduce((total, item) => total + item, 0) / scores.length);
  }

  commit(validation: Transition[]): boolean {
    const score = this.evaluate(validation);
    if (this.bestScoreValue === null || score >= this.bestScoreValue) {
      this.bestScoreValue = score;
      this.best = this.snapshot();
      this.history.push([score, true]);
      return true;
    }
    if (this.best) this.restoreCounts(this.best);
    this.history.push([score, false]);
    return false;
  }

  snapshot(): Snapshot {
    return {
      counts: [...this.counts.values()]
        .map((item) => ({ ...item }))
        .sort((left, right) =>
          transitionKey(left.state, left.action, left.nextState) <
          transitionKey(right.state, right.action, right.nextState)
            ? -1
            : 1,
        ),
      rewards: [...this.rewards.entries()]
        .sort(([left], [right]) => (left < right ? -1 : 1))
        .map(([pair, reward]) => {
          const [state, action] = pair.split("\u0000") as [string, string];
          return { state, action, reward };
        }),
      totals: [...this.totals.entries()]
        .sort(([left], [right]) => (left < right ? -1 : 1))
        .map(([pair, total]) => {
          const [state, action] = pair.split("\u0000") as [string, string];
          return { state, action, total };
        }),
    };
  }

  restore(snapshot: Snapshot): void {
    this.restoreCounts(snapshot);
  }

  toMdpModel(
    options: {
      states?: string[];
      actions?: string[];
      start?: string;
      discount?: number;
      horizon?: number | null;
    } = {},
  ): MdpModel {
    const learned = this.learned();
    if (!learned.length) throw new Error("no transitions have been learned");
    const nextStates = new Set(
      learned.flatMap((item) => Object.keys(item.probabilities)),
    );
    const knownStates = options.states ?? [
      ...new Set([...learned.map((item) => item.state), ...nextStates]),
    ].sort();
    const knownActions = options.actions ?? [...new Set(learned.map((item) => item.action))].sort();
    const transitions = learned.flatMap((item) => {
      const total = Object.values(item.probabilities).reduce(
        (sum, value) => sum + value,
        0,
      );
      if (total <= 0) return [];
      return Object.entries(item.probabilities)
        .filter(([, probability]) => probability > 0)
        .map(([nextState, probability]) => ({
          state: item.state,
          action: item.action,
          nextState,
          probability: probability / total,
          reward: item.expectedReward,
        }));
    });
    const model: MdpModelOptions = {
      states: knownStates,
      actions: knownActions,
      transitions,
      start: options.start ?? knownStates[0]!,
      discount: options.discount,
      horizon: options.horizon,
    };
    return new MdpModel(model);
  }

  private restoreCounts(snapshot: Snapshot): void {
    this.counts = new Map(
      snapshot.counts.map((item) => [
        transitionKey(item.state, item.action, item.nextState),
        { ...item },
      ]),
    );
    this.rewards = new Map(
      snapshot.rewards.map((item) => [pairKey(item.state, item.action), item.reward]),
    );
    this.totals = new Map(
      snapshot.totals.map((item) => [pairKey(item.state, item.action), item.total]),
    );
  }
}
