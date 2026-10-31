import type { Action, Decision, Receipt } from "../contracts.ts";
import { newId } from "../contracts.ts";

export type Handler = (action: Action, context: Record<string, unknown>) => Record<string, unknown>;

export class ApprovalRequired extends Error {}
export class UnknownAction extends Error {}

interface DecisionLike {
  decisionId?: string;
  id?: string;
  requiresApproval?: boolean;
}

export class ExecutionBridge {
  handlers = new Map<string, Handler>();
  undoHandlers = new Map<string, Handler>();
  receipts = new Map<string, Receipt>();

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

  execute(decision: DecisionLike, options: { action: Action | null; actor: string; approver?: string | null; context?: Record<string, unknown> }): Receipt {
    const decisionId = decision.decisionId ?? decision.id ?? "";
    const action = options.action;
    if (!action) {
      return this.store({ id: newId("RCT"), decisionId, actionName: "", status: "refused", actor: options.actor, error: "decision has no action to execute", at: new Date().toISOString() });
    }
    if (decision.requiresApproval && !options.approver) {
      throw new ApprovalRequired(`${action.name} requires human approval`);
    }
    const handler = this.handlers.get(action.name);
    if (!handler) {
      return this.store({ id: newId("RCT"), decisionId, actionName: action.name, status: "failed", actor: options.actor, error: `no handler registered for ${action.name}`, approvedBy: options.approver ?? null, at: new Date().toISOString() });
    }
    try {
      const detail = handler(action, { ...(options.context ?? {}) });
      return this.store({ id: newId("RCT"), decisionId, actionName: action.name, status: "executed", actor: options.actor, detail, approvedBy: options.approver ?? null, at: new Date().toISOString() });
    } catch (error) {
      return this.store({ id: newId("RCT"), decisionId, actionName: action.name, status: "failed", actor: options.actor, error: error instanceof Error ? `${error.name}: ${error.message}` : String(error), approvedBy: options.approver ?? null, at: new Date().toISOString() });
    }
  }

  refuse(decision: DecisionLike, options: { action: Action | null; actor: string; reason: string }): Receipt {
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

  get(receiptId: string): Receipt {
    const receipt = this.receipts.get(receiptId);
    if (!receipt) throw new Error(`unknown receipt ${receiptId}`);
    return receipt;
  }

  private store(receipt: Receipt): Receipt {
    this.receipts.set(receipt.id, receipt);
    return receipt;
  }
}
