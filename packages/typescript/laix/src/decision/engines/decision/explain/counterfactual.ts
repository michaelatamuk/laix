import type { Decision } from "../../../contracts.ts";

export type CounterfactualComponent =
  | "utility"
  | "commitment"
  | "execution"
  | "human_attention";

export interface Counterfactual {
  alternativeId: string;
  component: CounterfactualComponent;
  delta: number;
  chosenTotal: number;
  alternativeTotal: number;
  resultingTotal: number;
  explanation: string;
}

export interface CounterfactualReport {
  chosenId: string;
  chosenTotal: number;
  counterfactuals: Counterfactual[];
  minimal: Counterfactual | null;
}

const COMPONENT_KEYS: Record<CounterfactualComponent, string> = {
  utility: "utility",
  commitment: "commitment_score",
  execution: "execution_score",
  human_attention: "human_attention_score",
};

const ALTERNATIVE_KEYS: Record<CounterfactualComponent, string> = {
  utility: "utility",
  commitment: "commitment",
  execution: "execution",
  human_attention: "human_attention",
};

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export function counterfactualAttribution(
  decision: Decision,
  options: {
    components?: CounterfactualComponent[];
    margin?: number;
  } = {},
): CounterfactualReport {
  const chosenId = decision.actionId ?? "chosen";
  const chosenTotal = Number(decision.score ?? 0);
  const attributes = decision.attributes ?? {};
  const requested = options.components ?? [
    "utility",
    "commitment",
    "execution",
    "human_attention",
  ];
  const available = requested.filter(
    (component) => COMPONENT_KEYS[component] in attributes,
  );
  const alternatives = decision.alternatives ?? [];
  if (!available.length || !alternatives.length) {
    return {
      chosenId,
      chosenTotal: round(chosenTotal),
      counterfactuals: [],
      minimal: null,
    };
  }
  const margin = options.margin ?? 1e-6;
  const rows: Counterfactual[] = [];
  for (const alternative of alternatives) {
    const alternativeId = String(
      alternative.action_id ?? alternative.actionId ?? "",
    );
    const alternativeTotal = Number(alternative.total ?? 0);
    const gap = chosenTotal - alternativeTotal;
    if (gap <= 0) continue;
    for (const component of available) {
      const alternativeKey = ALTERNATIVE_KEYS[component];
      if (alternative[alternativeKey] === undefined) continue;
      const delta = Math.max(0, gap + margin);
      rows.push({
        alternativeId,
        component,
        delta: round(delta),
        chosenTotal: round(chosenTotal),
        alternativeTotal: round(alternativeTotal),
        resultingTotal: round(alternativeTotal + delta),
        explanation: `${alternativeId} overtakes ${chosenId} if ${component} increases by ${delta.toFixed(6)}`,
      });
    }
  }
  rows.sort((left, right) =>
    left.delta !== right.delta
      ? left.delta - right.delta
      : left.alternativeId !== right.alternativeId
        ? left.alternativeId < right.alternativeId
          ? -1
          : 1
        : left.component < right.component
          ? -1
          : 1,
  );
  return {
    chosenId,
    chosenTotal: round(chosenTotal),
    counterfactuals: rows,
    minimal: rows[0] ?? null,
  };
}
