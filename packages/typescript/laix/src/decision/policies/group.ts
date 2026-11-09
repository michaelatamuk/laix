import type { Decision, DecisionRequest, TargetMode } from "../contracts.ts";
import { TARGET_MODES } from "../contracts.ts";

export interface GroupPolicyOptions {
  target?: TargetMode;
  recipients?: string[];
  privateAttributes?: string[];
  privateEvidence?: string[];
  rationale?: string;
  undoHint?: string;
}

export class GroupPolicy {
  readonly name = "group.v1";
  readonly policy: { decide(request: DecisionRequest): Decision[] };
  readonly target: TargetMode;
  readonly recipients: string[];
  readonly privateAttributes: Set<string>;
  readonly privateEvidence: Set<string>;
  readonly rationale: string | undefined;
  readonly undoHint: string | undefined;

  constructor(
    policy: { decide(request: DecisionRequest): Decision[] },
    options: GroupPolicyOptions = {},
  ) {
    const target = options.target ?? "some";
    if (!TARGET_MODES.includes(target)) {
      throw new Error(`unknown target mode: ${target}`);
    }
    this.policy = policy;
    this.target = target;
    this.recipients = [...(options.recipients ?? [])];
    this.privateAttributes = new Set(options.privateAttributes ?? []);
    this.privateEvidence = new Set(options.privateEvidence ?? []);
    this.rationale = options.rationale;
    this.undoHint = options.undoHint;
  }

  decide(request: DecisionRequest): Decision[] {
    const recipients = this.recipients.length
      ? this.recipients
      : [...(request.recipients ?? [])];
    return this.policy.decide(request).map((decision) => this.mask(decision, recipients));
  }

  private mask(decision: Decision, recipients: string[]): Decision {
    const evidence = (decision.evidence ?? []).filter(
      (item) =>
        !(
          this.privateEvidence.has(item.id) ||
          this.privateEvidence.has(item.kind ?? "") ||
          this.privateEvidence.has(item.source ?? "")
        ),
    );
    const intent = decision.intent
      ? {
          ...decision.intent,
          args: this.maskValue(decision.intent.args ?? {}) as Record<string, unknown>,
        }
      : decision.intent;
    return {
      ...decision,
      target: this.target,
      recipients,
      rationale: this.rationale ?? decision.rationale,
      undoHint: this.undoHint ?? decision.undoHint,
      evidence,
      intent,
      alternatives: (decision.alternatives ?? []).map(
        (item) => this.maskValue(item) as Record<string, unknown>,
      ),
      attributes: this.maskValue(decision.attributes ?? {}) as Record<string, unknown>,
    };
  }

  private maskValue(value: unknown): unknown {
    if (Array.isArray(value)) return value.map((item) => this.maskValue(item));
    if (value && typeof value === "object") {
      return Object.fromEntries(
        Object.entries(value as Record<string, unknown>)
          .filter(([key]) => !this.privateAttributes.has(key))
          .map(([key, item]) => [key, this.maskValue(item)]),
      );
    }
    return value;
  }
}
