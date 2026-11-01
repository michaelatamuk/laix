export const DELIVERY_STATUSES = ["delivered", "skipped", "failed"] as const;
export type DeliveryStatus = (typeof DELIVERY_STATUSES)[number];

export interface DeliveryReceipt {
  id: string;
  decisionId: string;
  channel: string;
  status: DeliveryStatus;
  at?: string;
  detail?: Record<string, unknown>;
}

export interface DeliveryPort {
  deliver(decision: { decisionId?: string }, message: unknown, options?: { channel?: string }): DeliveryReceipt;
}

export class NullDelivery implements DeliveryPort {
  receipts: DeliveryReceipt[] = [];

  deliver(decision: { decisionId?: string }, message: unknown, options: { channel?: string } = {}): DeliveryReceipt {
    const receipt: DeliveryReceipt = {
      id: `dl-${this.receipts.length + 1}`,
      decisionId: decision.decisionId ?? "",
      channel: options.channel ?? "default",
      status: "skipped",
      at: new Date().toISOString(),
      detail: { message },
    };
    this.receipts.push(receipt);
    return receipt;
  }

  toDict(): Record<string, unknown> {
    return { receipts: [...this.receipts] };
  }
}
