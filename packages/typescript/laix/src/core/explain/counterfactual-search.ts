export interface CounterfactualVariable {
  name: string;
  value: number;
  lower: number;
  upper: number;
  step?: number;
  weight?: number;
}

export interface CounterfactualChange {
  name: string;
  old: number;
  new: number;
  delta: number;
}

export interface CounterfactualSearchResult {
  chosenId: string;
  counterfactualId: string | null;
  changes: CounterfactualChange[];
  distance: number;
  evaluations: number;
}

function round(value: number): number {
  return Math.round(value * 1e9) / 1e9;
}

function grid(variable: CounterfactualVariable): number[] {
  const step = variable.step ?? 0.1;
  if (step <= 0) throw new Error("step must be positive");
  if (variable.lower > variable.upper) throw new Error("lower must not exceed upper");
  if (variable.value < variable.lower || variable.value > variable.upper) {
    throw new Error("value must be inside [lower, upper]");
  }
  const count = Math.round((variable.upper - variable.lower) / step);
  const values = new Set<number>();
  for (let index = 0; index <= count; index += 1) {
    values.add(round(variable.lower + index * step));
  }
  values.add(round(variable.value));
  return [...values].sort((left, right) => left - right);
}

function combinations<T>(items: T[], size: number): T[][] {
  if (size < 1 || size > items.length) return [];
  if (size === 1) return items.map((item) => [item]);
  const result: T[][] = [];
  for (let index = 0; index <= items.length - size; index += 1) {
    for (const rest of combinations(items.slice(index + 1), size - 1)) {
      result.push([items[index]!, ...rest]);
    }
  }
  return result;
}

function product(values: number[][]): number[][] {
  if (!values.length) return [[]];
  const [first, ...rest] = values;
  const tails = product(rest);
  const result: number[][] = [];
  for (const value of first!) {
    for (const tail of tails) result.push([value, ...tail]);
  }
  return result;
}

export function counterfactualSearch(
  decide: (values: Record<string, number>) => string,
  variables: CounterfactualVariable[],
  options: { maxChanges?: number; maxEvaluations?: number } = {},
): CounterfactualSearchResult {
  const maxChanges = options.maxChanges ?? 2;
  const maxEvaluations = options.maxEvaluations ?? 20000;
  if (maxChanges < 1) throw new Error("maxChanges must be at least one");
  if (maxEvaluations < 1) throw new Error("maxEvaluations must be at least one");
  const base = Object.fromEntries(variables.map((variable) => [variable.name, variable.value]));
  const chosen = decide(base);
  const grids = Object.fromEntries(
    variables.map((variable) => [variable.name, grid(variable)]),
  );
  const candidates: Array<{
    distance: number;
    names: string[];
    values: number[];
  }> = [];
  for (let size = 1; size <= Math.min(maxChanges, variables.length); size += 1) {
    for (const group of combinations(variables, size)) {
      const names = group.map((variable) => variable.name);
      for (const values of product(names.map((name) => grids[name]!))) {
        let distance = 0;
        let changed = false;
        for (let index = 0; index < names.length; index += 1) {
          const variable = group[index]!;
          const value = values[index]!;
          if (Math.abs(value - variable.value) > 1e-12) {
            changed = true;
            distance += (variable.weight ?? 1) * Math.abs(value - variable.value);
          }
        }
        if (changed) candidates.push({ distance: round(distance), names, values });
      }
    }
  }
  candidates.sort((left, right) => {
    if (left.distance !== right.distance) return left.distance - right.distance;
    const leftKey = left.names.join("\u0000");
    const rightKey = right.names.join("\u0000");
    if (leftKey !== rightKey) return leftKey < rightKey ? -1 : 1;
    return left.values.join(",") < right.values.join(",") ? -1 : 1;
  });
  let evaluations = 0;
  for (const candidate of candidates) {
    if (evaluations >= maxEvaluations) break;
    const probe = { ...base };
    candidate.names.forEach((name, index) => {
      probe[name] = candidate.values[index]!;
    });
    const result = decide(probe);
    evaluations += 1;
    if (result === chosen) continue;
    const changes = candidate.names
      .map((name, index) => ({
        name,
        old: round(base[name]!),
        new: round(candidate.values[index]!),
        delta: round(candidate.values[index]! - base[name]!),
      }))
      .filter((change) => Math.abs(change.delta) > 1e-12);
    return {
      chosenId: chosen,
      counterfactualId: result,
      changes,
      distance: candidate.distance,
      evaluations,
    };
  }
  return {
    chosenId: chosen,
    counterfactualId: null,
    changes: [],
    distance: 0,
    evaluations,
  };
}
