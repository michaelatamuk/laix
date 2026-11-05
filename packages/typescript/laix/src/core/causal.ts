export type CausalMethod = "difference-in-means" | "inverse-propensity";

export interface CausalObservation {
  decisionId: string;
  arm: string;
  outcome: number;
  propensity?: number | null;
  context?: Record<string, unknown>;
}

export interface CausalEffect {
  treatment: string;
  control: string;
  estimate: number;
  treated: number;
  controlSize: number;
  method: CausalMethod;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function weightedMean(
  items: CausalObservation[],
  weight: (propensity: number) => number,
): number {
  let total = 0;
  for (const item of items) {
    if (item.propensity === undefined || item.propensity === null) {
      throw new Error("propensity is required for weighting");
    }
    total += item.outcome * weight(item.propensity);
  }
  return total / items.length;
}

export class CausalLedger {
  records: CausalObservation[] = [];

  add(
    decisionId: string,
    options: {
      arm: string;
      outcome: number;
      propensity?: number | null;
      context?: Record<string, unknown>;
    },
  ): CausalObservation {
    const propensity = options.propensity ?? null;
    if (propensity !== null && (propensity < 0 || propensity > 1)) {
      throw new Error("propensity must be between zero and one");
    }
    const observation: CausalObservation = {
      decisionId,
      arm: options.arm,
      outcome: Number(options.outcome),
      propensity,
      context: { ...(options.context ?? {}) },
    };
    this.records.push(observation);
    return observation;
  }

  effect(treatment: string, control: string): CausalEffect {
    const treated = this.records.filter((item) => item.arm === treatment);
    const controlled = this.records.filter((item) => item.arm === control);
    if (!treated.length || !controlled.length) {
      throw new Error("both arms need at least one observation");
    }

    const weighted = [...treated, ...controlled].every(
      (item) =>
        item.propensity !== undefined &&
        item.propensity !== null &&
        item.propensity > 0 &&
        item.propensity < 1,
    );
    let treatedMean: number;
    let controlMean: number;
    let method: CausalMethod;
    if (weighted) {
      treatedMean = weightedMean(treated, (value) => 1 / value);
      controlMean = weightedMean(controlled, (value) => 1 / (1 - value));
      method = "inverse-propensity";
    } else {
      treatedMean = treated.reduce((total, item) => total + item.outcome, 0) / treated.length;
      controlMean = controlled.reduce((total, item) => total + item.outcome, 0) / controlled.length;
      method = "difference-in-means";
    }

    return {
      treatment,
      control,
      estimate: round(treatedMean - controlMean),
      treated: treated.length,
      controlSize: controlled.length,
      method,
    };
  }
}
