import type { Decision, DecisionRequest } from "../contracts.ts";
import { PolicyError } from "./policy-error.ts";

export { PolicyError };

export interface Policy {
  name: string;
  decide(request: DecisionRequest): Decision[];
}

export class PolicyRegistry {
  private policies = new Map<string, Policy>();

  register(name: string, policy: Policy): void {
    const key = name.trim();
    if (!key) throw new PolicyError("policy name is required");
    if (typeof policy.decide !== "function") throw new PolicyError(`policy '${key}' has no decide method`);
    this.policies.set(key, policy);
  }

  get(name: string): Policy {
    const policy = this.policies.get(name);
    if (!policy) {
      const known = [...this.policies.keys()].sort().join(", ") || "none";
      throw new PolicyError(`unknown policy ${name}; registered: ${known}`);
    }
    return policy;
  }

  names(): string[] {
    return [...this.policies.keys()].sort();
  }
}
