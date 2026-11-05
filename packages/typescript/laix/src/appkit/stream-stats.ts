export class StreamStats {
  observed = 0;
  decided = 0;
  late = 0;
  throttled = 0;
  dropped = 0;
  expired = 0;
  suppressed = 0;
  shed = 0;
  duplicates = 0;
  refineTimeouts = 0;
  provisional = 0;
  revised = 0;
  latencyP50 = 0;
  latencyP95 = 0;
  latencyP99 = 0;

  snapshot(): Record<string, number> {
    return {
      observed: this.observed,
      decided: this.decided,
      late: this.late,
      throttled: this.throttled,
      dropped: this.dropped,
      expired: this.expired,
      suppressed: this.suppressed,
      shed: this.shed,
      duplicates: this.duplicates,
      refineTimeouts: this.refineTimeouts,
      provisional: this.provisional,
      revised: this.revised,
      latencyP50: this.latencyP50,
      latencyP95: this.latencyP95,
      latencyP99: this.latencyP99,
    };
  }

  copy(): StreamStats {
    const copy = new StreamStats();
    copy.observed = this.observed;
    copy.decided = this.decided;
    copy.late = this.late;
    copy.throttled = this.throttled;
    copy.dropped = this.dropped;
    copy.expired = this.expired;
    copy.suppressed = this.suppressed;
    copy.shed = this.shed;
    copy.duplicates = this.duplicates;
    copy.refineTimeouts = this.refineTimeouts;
    copy.provisional = this.provisional;
    copy.revised = this.revised;
    copy.latencyP50 = this.latencyP50;
    copy.latencyP95 = this.latencyP95;
    copy.latencyP99 = this.latencyP99;
    return copy;
  }
}
