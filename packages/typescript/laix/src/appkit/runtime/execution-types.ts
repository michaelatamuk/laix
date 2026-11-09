import type { ActionOption, Decision, Receipt } from "../../decision/contracts.ts";

export type Handler = (action: ActionOption, context: Record<string, unknown>) => Record<string, unknown>;
export type AsyncHandler = (action: ActionOption, context: Record<string, unknown>) => Promise<Record<string, unknown>>;

export interface RetryOptions {
  attempts?: number;
  backoffMs?: number;
  maxBackoffMs?: number;
}

export class ExecutionTimeout extends Error {
  constructor(timeoutMs: number) {
    super(`action did not finish within ${timeoutMs}ms`);
    this.name = "ExecutionTimeout";
  }
}

export interface ExecutionStep {
  action: ActionOption;
  decision?: Decision;
  actor?: string;
  approver?: string | null;
  context?: Record<string, unknown>;
  idempotencyKey?: string;
  compensate?: (receipt: Receipt) => Record<string, unknown>;
  asyncCompensate?: (receipt: Receipt) => Promise<Record<string, unknown>>;
}

export interface ExecutionSagaResult {
  completed: string[];
  compensated: string[];
  receipts: Receipt[];
  error?: string | null;
  toDict(): Record<string, unknown>;
}
