export interface WhittleTransition {
  state: string;
  nextState: string;
  probability?: number;
}

export interface WhittleCandidate {
  id: string;
  states: string[];
  start: string;
  activeTransitions: WhittleTransition[];
  passiveTransitions: WhittleTransition[];
  activeReward?: Record<string, number>;
  passiveReward?: Record<string, number>;
  activeCost?: number;
  reviewCost?: number;
  discount?: number;
}

export interface WhittleRow {
  candidateId: string;
  index: number;
  selected: boolean;
  reviewCost: number;
  reason: string;
}

export interface WhittleSchedule {
  budget: number;
  spent: number;
  rows: WhittleRow[];
  selected: WhittleRow[];
  deferred: WhittleRow[];
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function rows(
  transitions: WhittleTransition[],
  state: string,
): Required<WhittleTransition>[] {
  return transitions
    .filter((item) => item.state === state)
    .map((item) => ({
      state: item.state,
      nextState: item.nextState,
      probability: item.probability ?? 1,
    }));
}

function expectation(
  transitions: WhittleTransition[],
  state: string,
  values: Record<string, number>,
): number {
  return rows(transitions, state).reduce(
    (total, item) => total + item.probability * (values[item.nextState] ?? 0),
    0,
  );
}

function values(candidate: WhittleCandidate, subsidy: number): Record<string, number> {
  let current = Object.fromEntries(candidate.states.map((state) => [state, 0]));
  const discount = candidate.discount ?? 0.9;
  const activeCost = candidate.activeCost ?? 0;
  for (let iteration = 0; iteration < 1000; iteration += 1) {
    const updated: Record<string, number> = {};
    let delta = 0;
    for (const state of candidate.states) {
      const active =
        (candidate.activeReward?.[state] ?? 0) -
        activeCost +
        discount * expectation(candidate.activeTransitions, state, current);
      const passive =
        (candidate.passiveReward?.[state] ?? 0) +
        subsidy +
        discount * expectation(candidate.passiveTransitions, state, current);
      updated[state] = Math.max(active, passive);
      delta = Math.max(delta, Math.abs(updated[state]! - (current[state] ?? 0)));
    }
    current = updated;
    if (delta < 1e-9) return current;
  }
  return current;
}

function passiveIsBetter(candidate: WhittleCandidate, subsidy: number): boolean {
  const current = values(candidate, subsidy);
  const state = candidate.start;
  const discount = candidate.discount ?? 0.9;
  const active =
    (candidate.activeReward?.[state] ?? 0) -
    (candidate.activeCost ?? 0) +
    discount * expectation(candidate.activeTransitions, state, current);
  const passive =
    (candidate.passiveReward?.[state] ?? 0) +
    subsidy +
    discount * expectation(candidate.passiveTransitions, state, current);
  return passive >= active;
}

export function whittleIndex(
  candidate: WhittleCandidate,
  options: { lower?: number; upper?: number; iterations?: number } = {},
): number {
  const lower = options.lower ?? -10;
  const upper = options.upper ?? 10;
  if (passiveIsBetter(candidate, lower)) return round(lower);
  if (!passiveIsBetter(candidate, upper)) return round(upper);
  let low = lower;
  let high = upper;
  const iterations = Math.max(1, options.iterations ?? 60);
  for (let index = 0; index < iterations; index += 1) {
    const mid = (low + high) / 2;
    if (passiveIsBetter(candidate, mid)) high = mid;
    else low = mid;
  }
  return round((low + high) / 2);
}

export class WhittleScheduler {
  readonly name = "aads.whittle.v1";
  private readonly lower: number;
  private readonly upper: number;
  private readonly iterations: number;

  constructor(
    options: { lower?: number; upper?: number; iterations?: number } = {},
  ) {
    this.lower = options.lower ?? -10;
    this.upper = options.upper ?? 10;
    this.iterations = options.iterations ?? 60;
  }

  schedule(
    candidates: WhittleCandidate[],
    options: { budget?: number } = {},
  ): WhittleSchedule {
    const limit = Math.max(0, options.budget ?? 1);
    const ordered = candidates
      .map((candidate) => ({
        candidate,
        index: whittleIndex(candidate, {
          lower: this.lower,
          upper: this.upper,
          iterations: this.iterations,
        }),
      }))
      .sort((left, right) =>
        right.index !== left.index
          ? right.index - left.index
          : left.candidate.id < right.candidate.id
            ? -1
            : 1,
      );
    let spent = 0;
    const rows: WhittleRow[] = ordered.map(({ candidate, index }) => {
      const reviewCost = Math.max(1e-9, candidate.reviewCost ?? 1);
      const selected = spent + reviewCost <= limit + 1e-9;
      if (selected) spent += reviewCost;
      return {
        candidateId: candidate.id,
        index,
        selected,
        reviewCost: round(reviewCost),
        reason: selected
          ? "within attention budget"
          : "attention budget exhausted",
      };
    });
    return {
      budget: round(limit),
      spent: round(spent),
      rows,
      selected: rows.filter((row) => row.selected),
      deferred: rows.filter((row) => !row.selected),
    };
  }
}
