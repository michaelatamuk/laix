import type { Decision, DecisionRequest, TargetMode } from "../contracts.ts";
import { TARGET_MODES } from "../contracts.ts";

export interface GroupPolicyOptions {
  target?: TargetMode;
  recipients?: string[];
  privateAttributes?: string[];
}

export class GroupPolicy {
  readonly name = "group.v1";
  readonly policy: { decide(request: DecisionRequest): Decision[] };
  readonly target: TargetMode;
  readonly recipients: string[];
  readonly privateAttributes: Set<string>;

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
  }

  decide(request: DecisionRequest): Decision[] {
    const recipients = this.recipients.length
      ? this.recipients
      : [...(request.recipients ?? [])];
    return this.policy.decide(request).map((decision) => ({
      ...decision,
      target: this.target,
      recipients,
      attributes: Object.fromEntries(
        Object.entries(decision.attributes ?? {}).filter(
          ([key]) => !this.privateAttributes.has(key),
        ),
      ),
    }));
  }
}
