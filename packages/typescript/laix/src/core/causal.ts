import type { Outcome } from "./contracts.ts";

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
  standardError?: number;
  ciLow?: number;
  ciHigh?: number;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function variance(values: number[], mean: number): number {
  if (values.length < 2) return 0;
  return values.reduce((total, value) => total + (value - mean) ** 2, 0) / (values.length - 1);
}

function weightedVariance(
  items: CausalObservation[],
  weight: (propensity: number) => number,
  mean: number,
): number {
  if (items.length < 2) return 0;
  let total = 0;
  for (const item of items) {
    if (item.propensity === undefined || item.propensity === null) {
      throw new Error("propensity is required for weighting");
    }
    total += weight(item.propensity) ** 2 * (item.outcome - mean) ** 2;
  }
  return total / items.length ** 2;
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

  addOutcome(
    outcome: Outcome,
    options: {
      arm: string;
      propensity?: number | null;
      context?: Record<string, unknown>;
      signed?: boolean;
    },
  ): CausalObservation {
    const signed = options.signed ?? true;
    const value =
      signed && outcome.direction === "lower-better"
        ? -outcome.delta
        : outcome.delta;
    return this.add(outcome.decisionId, {
      arm: options.arm,
      outcome: value,
      propensity: options.propensity,
      context: options.context,
    });
  }

  static fromOutcomes(
    outcomes: Outcome[],
    arms: Record<string, string>,
    options: {
      defaultArm?: string;
      propensities?: Record<string, number>;
      contexts?: Record<string, Record<string, unknown>>;
      signed?: boolean;
    } = {},
  ): CausalLedger {
    const ledger = new CausalLedger();
    for (const outcome of outcomes) {
      const arm = arms[outcome.decisionId] ?? options.defaultArm;
      if (arm === undefined) continue;
      ledger.addOutcome(outcome, {
        arm,
        propensity: options.propensities?.[outcome.decisionId],
        context: options.contexts?.[outcome.decisionId],
        signed: options.signed,
      });
    }
    return ledger;
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
    let treatedVariance: number;
    let controlVariance: number;
    let method: CausalMethod;
    if (weighted) {
      treatedMean = weightedMean(treated, (value) => 1 / value);
      controlMean = weightedMean(controlled, (value) => 1 / (1 - value));
      treatedVariance = weightedVariance(treated, (value) => 1 / value, treatedMean);
      controlVariance = weightedVariance(controlled, (value) => 1 / (1 - value), controlMean);
      method = "inverse-propensity";
    } else {
      treatedMean = treated.reduce((total, item) => total + item.outcome, 0) / treated.length;
      controlMean = controlled.reduce((total, item) => total + item.outcome, 0) / controlled.length;
      treatedVariance = variance(treated.map((item) => item.outcome), treatedMean) / treated.length;
      controlVariance = variance(controlled.map((item) => item.outcome), controlMean) / controlled.length;
      method = "difference-in-means";
    }

    const estimate = round(treatedMean - controlMean);
    const standardError = round(Math.sqrt(treatedVariance + controlVariance));
    return {
      treatment,
      control,
      estimate,
      treated: treated.length,
      controlSize: controlled.length,
      method,
      standardError,
      ciLow: round(estimate - 1.96 * standardError),
      ciHigh: round(estimate + 1.96 * standardError),
    };
  }

  effectByContext(
    treatment: string,
    control: string,
    options: { key?: string } = {},
  ): Record<string, CausalEffect> {
    const key = options.key ?? "stratum";
    const buckets = new Map<string, CausalObservation[]>();
    for (const item of this.records) {
      const stratum = String(item.context?.[key] ?? "all");
      const items = buckets.get(stratum) ?? [];
      items.push(item);
      buckets.set(stratum, items);
    }
    const effects: Record<string, CausalEffect> = {};
    for (const [stratum, records] of [...buckets.entries()].sort(([left], [right]) =>
      left < right ? -1 : 1,
    )) {
      const arms = new Set(records.map((item) => item.arm));
      if (!arms.has(treatment) || !arms.has(control)) continue;
      const ledger = new CausalLedger();
      ledger.records = records;
      effects[stratum] = ledger.effect(treatment, control);
    }
    return effects;
  }
}
