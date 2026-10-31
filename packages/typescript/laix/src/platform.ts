export const CAPABILITY_LEVELS = ["fast", "balanced", "deep"] as const;
export type CapabilityLevel = (typeof CAPABILITY_LEVELS)[number];

export interface SkillCall {
  capability: string;
  args?: Record<string, unknown>;
  traceId?: string;
}

export interface ApprovalRequest {
  decisionId: string;
  action: string;
  rationale?: string;
  risk?: number;
  reversible?: boolean;
  evidence?: string[];
}

export interface ApprovalDecision {
  approved: boolean;
  by?: string;
  at?: string;
  note?: string;
}

export interface Event {
  traceId: string;
  kind: string;
  at?: string;
  payload?: Record<string, unknown>;
}

export interface Capability {
  level: CapabilityLevel;
  modalities?: string[];
  maxLatencyMs?: number | null;
  maxCost?: number | null;
}

export interface Platform {
  runSkill(call: SkillCall): unknown;
  cancel(runId: string, reason?: string): boolean;
  requestApproval(request: ApprovalRequest): ApprovalDecision;
  readState(key: string): unknown;
  writeState(key: string, value: unknown): void;
  events(traceId: string): Event[];
  capability(level: string): Capability;
}

export class InMemoryPlatform implements Platform {
  private skills = new Map<string, (call: SkillCall) => unknown>();
  private state = new Map<string, unknown>();
  private log: Event[] = [];
  private approver?: (request: ApprovalRequest) => ApprovalDecision;
  private capabilities = new Map<string, Capability>([
    ["fast", { level: "fast", modalities: ["text"], maxLatencyMs: 200, maxCost: 0.001 }],
    ["balanced", { level: "balanced", modalities: ["text", "image"], maxLatencyMs: 1500, maxCost: 0.02 }],
    ["deep", { level: "deep", modalities: ["text", "image", "audio", "video"], maxLatencyMs: 15000, maxCost: 0.2 }],
  ]);

  constructor(options: { approver?: (request: ApprovalRequest) => ApprovalDecision } = {}) {
    this.approver = options.approver;
  }

  register(capability: string, handler: (call: SkillCall) => unknown): void {
    this.skills.set(capability, handler);
  }

  runSkill(call: SkillCall): unknown {
    const handler = this.skills.get(call.capability);
    if (!handler) throw new Error(`no skill registered for '${call.capability}'`);
    const traceId = call.traceId ?? "";
    this.log.push({ traceId, kind: "skill.started", at: new Date().toISOString(), payload: { capability: call.capability } });
    const result = handler(call);
    this.log.push({ traceId, kind: "skill.finished", at: new Date().toISOString(), payload: { capability: call.capability } });
    return result;
  }

  cancel(runId: string, reason = ""): boolean {
    this.log.push({ traceId: runId, kind: "skill.cancelled", at: new Date().toISOString(), payload: { reason } });
    return true;
  }

  requestApproval(request: ApprovalRequest): ApprovalDecision {
    const decision = this.approver?.(request) ?? { approved: false, note: "no approver configured" };
    this.log.push({ traceId: request.decisionId, kind: "approval.decided", at: new Date().toISOString(), payload: { approved: decision.approved, by: decision.by } });
    return decision;
  }

  readState(key: string): unknown {
    return this.state.get(key);
  }

  writeState(key: string, value: unknown): void {
    this.state.set(key, value);
  }

  events(traceId: string): Event[] {
    return this.log.filter((event) => event.traceId === traceId);
  }

  capability(level: string): Capability {
    const item = this.capabilities.get(level);
    if (!item) throw new Error(`unknown capability level: '${level}'`);
    return item;
  }
}
