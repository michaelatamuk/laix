export class HumanAttentionBudget {
  total: number;
  spent: number;

  constructor(options: { total?: number; spent?: number } = {}) {
    this.total = options.total ?? 1;
    this.spent = options.spent ?? 0;
    if (this.total < 0) throw new Error("attention budget total must not be negative");
    if (this.spent < 0) throw new Error("attention budget spent must not be negative");
  }

  remaining(): number {
    return Math.max(0, this.total - this.spent);
  }

  spend(amount: number): number {
    if (amount < 0) throw new Error("attention spend must not be negative");
    this.spent = Math.min(this.total, this.spent + amount);
    return this.remaining();
  }

  toDict(): { total: number; spent: number } {
    return { total: this.total, spent: this.spent };
  }

  static fromDict(payload: { total?: number; spent?: number }): HumanAttentionBudget {
    return new HumanAttentionBudget({
      total: payload.total,
      spent: payload.spent,
    });
  }
}
