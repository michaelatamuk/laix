import type { Decision, DecisionRequest, TargetMode } from "../contracts.ts";

export class TargetedPolicy {
  readonly name = "targeted.v1";
  readonly policy: { decide(request: DecisionRequest): Decision[] };
  readonly target: "request" | TargetMode;
  readonly recipients: string[];

  constructor(
    policy: { decide(request: DecisionRequest): Decision[] },
    options: { target?: "request" | TargetMode; recipients?: string[] } = {},
  ) {
    this.policy = policy;
    this.target = options.target ?? "request";
    this.recipients = [...(options.recipients ?? [])];
  }

  decide(request: DecisionRequest): Decision[] {
    const target = this.target === "request" ? (request.target ?? "one") : this.target;
    const recipients = this.recipients.length ? this.recipients : [...(request.recipients ?? [])];
    return this.policy.decide(request).map((decision) => ({ ...decision, target, recipients }));
  }
}
