import type { Outcome } from "../../contracts.ts";

export interface OutcomeStore {
  add(outcome: Outcome): Outcome;
  forDecision(decisionId: string): Outcome[];
  all(): Outcome[];
  summary(): Record<string, unknown>;
}

export class OutcomeLedger implements OutcomeStore {
  records: Outcome[] = [];
  tolerance = 0.05;

  add(outcome: Outcome): Outcome {
    this.records.push(outcome);
    return outcome;
  }

  forDecision(decisionId: string): Outcome[] {
    return this.records.filter((item) => item.decisionId === decisionId);
  }

  all(): Outcome[] {
    return [...this.records];
  }

  summary(): Record<string, unknown> {
    const attributed = this.records.filter((item) => item.attributed);
    const helped = attributed.filter((item) => item.label === "helped");
    const hurt = attributed.filter((item) => item.label === "hurt");
    const gains = attributed.map((item) => (item.direction === "lower-better" ? -item.delta : item.delta));
    return {
      measured: this.records.length,
      attributed: attributed.length,
      attributionCoverage: Number((attributed.length / Math.max(1, this.records.length)).toFixed(3)),
      helped: helped.length,
      neutral: attributed.filter((item) => item.label === "neutral").length,
      hurt: hurt.length,
      meanGain: gains.length ? Number((gains.reduce((sum, item) => sum + item, 0) / gains.length).toFixed(6)) : 0,
      precision: Number((helped.length / Math.max(1, attributed.length)).toFixed(3)),
    };
  }

  byMetric(): Record<string, Record<string, number>> {
    const rows: Record<string, Record<string, number>> = {};
    for (const item of this.records) {
      const bucket = rows[item.metric] ?? { measured: 0, attributed: 0, helped: 0, hurt: 0, gain: 0 };
      bucket.measured += 1;
      if (item.attributed) {
        bucket.attributed += 1;
        bucket.helped += item.label === "helped" ? 1 : 0;
        bucket.hurt += item.label === "hurt" ? 1 : 0;
        bucket.gain += item.direction === "lower-better" ? -item.delta : item.delta;
      }
      rows[item.metric] = bucket;
    }
    for (const value of Object.values(rows)) value.gain = Number(value.gain.toFixed(6));
    return rows;
  }

  toDict(): Record<string, unknown> {
    return { tolerance: this.tolerance, records: [...this.records], summary: this.summary() };
  }
}
