import type { ActionOption, Decision, Outcome, Receipt, Situation, Trace } from "../../core/contracts.ts";
import { clamp, iso, newId } from "../../core/contracts.ts";
import { decideAction } from "../decision-client.ts";
import { OutcomeLedger } from "../../core/outcome.ts";
import { ApprovalRequired, ExecutionBridge } from "./execution.ts";
import { ResourceScheduler, type Budget, type ResourcePlan, type SensingOption } from "../../core/resources.ts";
import { ExperienceState } from "./state.ts";

export interface RuntimeDecision extends Decision {
  decisionId: string;
  createdAt: string;
}

export class DecisionRuntime {
  state: ExperienceState;
  bridge: ExecutionBridge;
  outcomes: OutcomeLedger;
  resources: ResourceScheduler;
  private decisions = new Map<string, RuntimeDecision>();
  private actions = new Map<string, ActionOption>();
  private traces = new Map<string, Trace>();
  private traceByDecision = new Map<string, string>();
  private receiptIds: string[] = [];

  constructor(options: { state?: ExperienceState; bridge?: ExecutionBridge; outcomes?: OutcomeLedger; resources?: ResourceScheduler } = {}) {
    this.state = options.state ?? new ExperienceState("");
    this.bridge = options.bridge ?? new ExecutionBridge();
    this.outcomes = options.outcomes ?? new OutcomeLedger();
    this.resources = options.resources ?? new ResourceScheduler();
  }

  observe(observation: Parameters<ExperienceState["observe"]>[0]): void {
    this.state.observe(observation);
  }

  decide(situation: Situation, options: ActionOption[], attributes: Record<string, unknown> = {}): RuntimeDecision {
    const base = decideAction({ ...situation, attributes: { ...(situation.attributes ?? {}), ...attributes } }, options);
    const decision: RuntimeDecision = { ...base, decisionId: newId("DEC"), createdAt: iso() };
    this.decisions.set(decision.decisionId, decision);
    for (const option of options) this.actions.set(option.id, option as unknown as ActionOption);
    this.state.record(decision as unknown as Decision);
    const traceId = decision.traceId || newId("TRC");
    const trace: Trace = { id: traceId, decisionId: decision.decisionId, events: [{ at: situation.at, stage: "situation", detail: { subject: situation.subject, options: options.map((item) => item.id), attributes } }] };
    trace.events.push({ at: iso(), stage: "decided", detail: { verb: decision.verb, action: decision.actionId, policy: "policy_rule", requiresApproval: decision.requiresApproval } });
    this.traces.set(traceId, trace);
    this.traceByDecision.set(decision.decisionId, traceId);
    return decision;
  }

  execute(decision: RuntimeDecision, options: { actor: string; approver?: string | null; context?: Record<string, unknown>; action?: ActionOption | null }): Receipt {
    const resolved = options.action ?? (decision.actionId ? this.actions.get(decision.actionId) ?? null : null);
    let receipt: Receipt;
    try {
      receipt = this.bridge.execute(decision, { action: resolved, actor: options.actor, approver: options.approver, context: options.context });
    } catch (error) {
      if (!(error instanceof ApprovalRequired)) throw error;
      receipt = this.bridge.refuse(decision, { action: resolved, actor: options.actor, reason: error.message });
    }
    this.receiptIds.push(receipt.id);
    this.appendTrace(decision, `execution.${receipt.status}`, { receipt: receipt.id, actor: options.actor, approvedBy: options.approver ?? null, error: receipt.error ?? null });
    return receipt;
  }

  cancel(receiptId: string, options: { actor: string; reason?: string }): Receipt {
    const receipt = this.bridge.cancel(receiptId, options);
    const decision = this.decisions.get(receipt.decisionId);
    if (decision) this.appendTrace(decision, "execution.cancelled", { receipt: receipt.id, actor: options.actor, reason: options.reason ?? "" });
    return receipt;
  }

  undo(receiptId: string, options: { actor: string }): Receipt {
    const receipt = this.bridge.undo(receiptId, options);
    const decision = this.decisions.get(receipt.decisionId);
    if (decision) this.appendTrace(decision, "execution.undone", { receipt: receipt.id, actor: options.actor });
    return receipt;
  }

  measure(decisionId: string, options: { metric: string; before: number; after: number; attributed?: boolean; direction?: Outcome["direction"]; note?: string }): Outcome {
    const direction = options.direction ?? "higher-better";
    const delta = options.after - options.before;
    const gain = direction === "lower-better" ? -delta : delta;
    const label: Outcome["label"] = gain > 0.05 ? "helped" : gain < -0.05 ? "hurt" : "neutral";
    const outcome: Outcome = { id: newId("OUT"), decisionId, metric: options.metric, before: options.before, after: options.after, delta, label, attributed: options.attributed ?? true, direction, measuredAt: iso(), note: options.note ?? "" };
    return this.outcomes.add(outcome);
  }

  schedule(options: SensingOption[], settings: { budget?: Budget; uncertainty?: number } = {}): ResourcePlan {
    return this.resources.schedule(options, { budget: settings.budget, uncertainty: settings.uncertainty ?? (1 - this.state.confidence()) });
  }

  trace(decisionId: string): Trace {
    const traceId = this.traceByDecision.get(decisionId);
    if (!traceId) {
      const trace = [...this.traces.values()].find((item) => item.decisionId === decisionId);
      if (!trace) throw new Error(`unknown decision ${decisionId}`);
      return trace;
    }
    return this.traces.get(traceId)!;
  }

  decision(decisionId: string): RuntimeDecision {
    const decision = this.decisions.get(decisionId);
    if (!decision) throw new Error(`unknown decision ${decisionId}`);
    return decision;
  }

  actionFor(decision: RuntimeDecision): ActionOption | null {
    return decision.actionId ? this.actions.get(decision.actionId) ?? null : null;
  }

  receipts(): Receipt[] {
    return this.receiptIds.map((id) => this.bridge.get(id));
  }

  stats(): Record<string, unknown> {
    return {
      decisions: this.decisions.size,
      receipts: this.receiptIds.length,
      traces: this.traces.size,
      outcomes: this.outcomes.records.length,
      phase: this.state.phase,
      confidence: Number(this.state.confidence().toFixed(3)),
    };
  }

  private appendTrace(decision: RuntimeDecision, stage: string, detail: Record<string, unknown>): void {
    const traceId = this.traceByDecision.get(decision.decisionId);
    if (!traceId) return;
    this.traces.get(traceId)?.events.push({ at: iso(), stage, detail });
  }
}
