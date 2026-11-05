export class ManualClock {
  now: Date;

  constructor(now: Date = new Date()) {
    this.now = now;
  }

  set(value: Date): void {
    this.now = value;
  }
}
