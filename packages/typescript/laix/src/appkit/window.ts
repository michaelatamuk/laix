import type { DecisionRequest } from "../core/contracts.ts";

export interface WindowBatch {
  start: Date;
  end: Date;
  events: DecisionRequest[];
}

export class TumblingWindow {
  readonly windowMs: number;
  readonly late: "drop" | "accept";
  private start: Date | null = null;
  private events: DecisionRequest[] = [];
  private watermark: number | null = null;

  constructor(windowMs: number, options: { late?: "drop" | "accept" } = {}) {
    if (windowMs <= 0) throw new Error("windowMs must be positive");
    this.windowMs = windowMs;
    this.late = options.late ?? "drop";
  }

  get pending(): number {
    return this.events.length;
  }

  add(event: DecisionRequest): WindowBatch[] {
    const at = Date.parse(event.at);
    if (Number.isNaN(at)) throw new Error(`event has no valid at: ${event.at}`);

    if (this.watermark !== null && at < this.watermark) {
      if (this.late === "drop") return [];
    } else {
      this.watermark = at;
    }

    const start = this.windowStart(at);
    const batches: WindowBatch[] = [];
    if (this.start === null) {
      this.start = start;
    } else if (start.getTime() > this.start.getTime()) {
      batches.push(this.close());
      this.start = start;
    } else if (start.getTime() < this.start.getTime() && this.late === "drop") {
      return [];
    }

    this.events.push(event);
    return batches;
  }

  flush(): WindowBatch[] {
    if (!this.events.length) return [];
    return [this.close()];
  }

  private close(): WindowBatch {
    if (this.start === null) throw new Error("window has no start");
    const batch: WindowBatch = {
      start: this.start,
      end: new Date(this.start.getTime() + this.windowMs),
      events: [...this.events],
    };
    this.events = [];
    return batch;
  }

  private windowStart(at: number): Date {
    return new Date(Math.floor(at / this.windowMs) * this.windowMs);
  }
}
