import type { ActionOption, Decision, Receipt } from "../../core/contracts.ts";
import { newId } from "../../core/contracts.ts";
import { ApprovalRequired } from "./approval-required.ts";
import { Saga, type SagaStep } from "./saga.ts";
import { UnknownAction } from "./unknown-action.ts";

export { ApprovalRequired, UnknownAction };

export type Handler = (action: ActionOption, context: Record<string, unknown>) => Record<string, unknown>;

export interface ExecutionStep {
  action: ActionOption;
  decision?: Decision;
  actor?: string;
  approver?: string | null;
  context?: Record<string, unknown>;
  idempotencyKey?: string;
  compensate?: (receipt: Receipt) => Record<string, unknown>;
}

export interface ExecutionSagaResult {
  completed: string[];
  compensated: string[];
  receipts: Receipt[];
  error?: string | null;
  toDict(): Record<string, unknown>;
}

interface DecisionLike {
  decisionId?: string;
  id?: string;
  requiresApproval?: boolean;
}

export class ExecutionBridge {
  handlers = new Map<string, Handler>();
  undoHandlers = new Map<string, Handler>();
  receipts = new Map<string, Receipt>();
  private byKey = new Map<string, string>();

  constructor(options: { handlers?: Record<string, Handler>; undoHandlers?: Record<string, Handler> } = {}) {
    for (const [name, handler] of Object.entries(options.handlers ?? {})) this.handlers.set(name, handler);
    for (const [name, handler] of Object.entries(options.undoHandlers ?? {})) this.undoHandlers.set(name, handler);
  }

  register(name: string, handler: Handler, undo?: Handler): void {
    this.handlers.set(name, handler);
    if (undo) this.undoHandlers.set(name, undo);
  }

  canHandle(name: string): boolean {
    return this.handlers.has(name);
  }

  canUndo(name: string): boolean {
    return this.undoHandlers.has(name);
  }

  runSteps(steps: ExecutionStep[], options: { actor?: string } = {}): ExecutionSagaResult {
    const actor = options.actor ?? "system";
    const receipts: Receipt[] = [];
    const completed = new Map<number, Receipt>();
    const failure: string[] = [];
    const sagaSteps: SagaStep[] = steps.map((step, index) => {
      const decision: Decision = step.decision ?? {
        verb: step.action.verb,
        confidence: 1,
        reasonCode: "execution_step",
        rationale: step.action.name,
      };
      const forward = (): Record<string, unknown> => {
        const receipt = this.execute(decision, {
          action: step.action,
          actor: step.actor ?? actor,
          approver: step.approver,
          context: step.context,
          idempotencyKey: step.idempotencyKey,
        });
        receipts.push(receipt);
        if (receipt.status === "executed" || receipt.status === "duplicate") {
          completed.set(index, receipt);
          return { ...(receipt.detail ?? {}) };
        }
        failure.push(receipt.error ?? `${step.action.name} did not execute`);
        throw new Error(failure[failure.length - 1]!);
      };
      let compensate: (() => Record<string, unknown>) | undefined;
      if (step.compensate) {
        compensate = () => {
          const receipt = completed.get(index);
          return receipt ? step.compensate!(receipt) : {};
        };
      } else if (this.canUndo(step.action.name)) {
        compensate = () => {
          const receipt = completed.get(index);
          if (!receipt) return {};
          return { ...(this.undo(receipt.id, { actor: step.actor ?? actor }).detail ?? {}) };
        };
      }
      return { name: step.action.name, forward, compensate };
    });

    const result = new Saga().run(sagaSteps);
    return {
      completed: result.completed,
      compensated: result.compensated,
      receipts,
      error: failure[0] ?? result.error,
      toDict(): Record<string, unknown> {
        return {
          completed: [...result.completed],
          compensated: [...result.compensated],
          receipts: receipts.map((item) => ({ ...item })),
          error: failure[0] ?? result.error ?? null,
        };
      },
    };
  }

  execute(decision: DecisionLike, options: { action: ActionOption | null; actor: string; approver?: string | null; context?: Record<string, unknown>; idempotencyKey?: string }): Receipt {
    const decisionId = decision.decisionId ?? decision.id ?? "";
    const action = options.action;
    const key = options.idempotencyKey;
    if (key && this.byKey.has(key)) {
      const original = this.get(this.byKey.get(key)!);
      return this.store({
        id: newId("RCT"),
        decisionId,
        actionName: action?.name ?? "",
        status: "duplicate",
        actor: options.actor,
        detail: { original: original.id },
        approvedBy: options.approver ?? null,
        idempotencyKey: key,
        at: new Date().toISOString(),
      });
    }
    if (!action) {
      return this.store({ id: newId("RCT"), decisionId, actionName: "", status: "refused", actor: options.actor, error: "decision has no action to execute", idempotencyKey: key ?? null, at: new Date().toISOString() });
    }
    if (decision.requiresApproval && !options.approver) {
      throw new ApprovalRequired(`${action.name} requires human approval`);
    }
    const handler = this.handlers.get(action.name);
    if (!handler) {
      return this.store({ id: newId("RCT"), decisionId, actionName: action.name, status: "failed", actor: options.actor, error: `no handler registered for ${action.name}`, approvedBy: options.approver ?? null, idempotencyKey: key ?? null, at: new Date().toISOString() });
    }
    try {
      const detail = handler(action, { ...(options.context ?? {}) });
      const receipt = this.store({ id: newId("RCT"), decisionId, actionName: action.name, status: "executed", actor: options.actor, detail, approvedBy: options.approver ?? null, idempotencyKey: key ?? null, at: new Date().toISOString() });
      if (key) this.byKey.set(key, receipt.id);
      return receipt;
    } catch (error) {
      return this.store({ id: newId("RCT"), decisionId, actionName: action.name, status: "failed", actor: options.actor, error: error instanceof Error ? `${error.name}: ${error.message}` : String(error), approvedBy: options.approver ?? null, idempotencyKey: key ?? null, at: new Date().toISOString() });
    }
  }

  refuse(decision: DecisionLike, options: { action: ActionOption | null; actor: string; reason: string }): Receipt {
    return this.store({
      id: newId("RCT"),
      decisionId: decision.decisionId ?? decision.id ?? "",
      actionName: options.action?.name ?? "",
      status: "refused",
      actor: options.actor,
      error: options.reason,
      at: new Date().toISOString(),
    });
  }

  cancel(receiptId: string, options: { actor: string; reason?: string }): Receipt {
    const receipt = this.get(receiptId);
    if (!["pending", "approved"].includes(receipt.status)) throw new Error(`cannot cancel a receipt that is ${receipt.status}`);
    return this.store({ ...receipt, status: "cancelled", actor: options.actor, detail: { ...(receipt.detail ?? {}), cancelReason: options.reason ?? "" } });
  }

  undo(receiptId: string, options: { actor: string }): Receipt {
    const receipt = this.get(receiptId);
    if (receipt.status !== "executed") throw new Error(`cannot undo a receipt that is ${receipt.status}`);
    const handler = this.undoHandlers.get(receipt.actionName);
    if (!handler) throw new Error(`no undo handler for ${receipt.actionName}`);
    const detail = handler({ id: receipt.id, verb: "act", name: receipt.actionName }, { receipt });
    return this.store({ ...receipt, status: "undone", actor: options.actor, detail: { ...(receipt.detail ?? {}), undo: detail }, previousState: receipt.detail });
  }

  markUnknown(receiptId: string, options: { actor: string; reason?: string }): Receipt {
    const receipt = this.get(receiptId);
    return this.store({
      ...receipt,
      status: "unknown",
      actor: options.actor,
      detail: { ...(receipt.detail ?? {}), unknownReason: options.reason ?? "" },
    });
  }

  reconcile(
    receiptId: string,
    options: { actor: string; status: "executed" | "failed" | "unknown"; detail?: Record<string, unknown> },
  ): Receipt {
    const receipt = this.get(receiptId);
    const reconciled = this.store({
      ...receipt,
      status: options.status,
      actor: options.actor,
      detail: { ...(receipt.detail ?? {}), ...(options.detail ?? {}) },
    });
    if (options.status === "executed" && reconciled.idempotencyKey) {
      this.byKey.set(reconciled.idempotencyKey, reconciled.id);
    }
    return reconciled;
  }

  get(receiptId: string): Receipt {
    const receipt = this.receipts.get(receiptId);
    if (!receipt) throw new Error(`unknown receipt ${receiptId}`);
    return receipt;
  }

  executionState(): Record<string, string> {
    const state: Record<string, string> = {};
    for (const receipt of this.receipts.values()) {
      state[receipt.actionName] = receipt.status;
    }
    return state;
  }

  private store(receipt: Receipt): Receipt {
    this.receipts.set(receipt.id, receipt);
    return receipt;
  }
}
