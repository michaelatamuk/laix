import type { Decision, DecisionRequest } from "../../../contracts.ts";
import { DecisionPolicyError } from "./decision-policy-error.ts";

export { DecisionPolicyError };

export interface DecisionPolicy {
  name: string;
  decide(request: DecisionRequest): Decision[];
}

export class DecisionPolicyRegistry {
  private policies = new Map<string, DecisionPolicy>();

  register(name: string, policy: DecisionPolicy): void {
    const key = name.trim();
    if (!key) throw new DecisionPolicyError("policy name is required");
    if (typeof policy.decide !== "function") throw new DecisionPolicyError(`policy '${key}' has no decide method`);
    this.policies.set(key, policy);
  }

  get(name: string): DecisionPolicy {
    const policy = this.policies.get(name);
    if (!policy) {
      const known = [...this.policies.keys()].sort().join(", ") || "none";
      throw new DecisionPolicyError(`unknown policy ${name}; registered: ${known}`);
    }
    return policy;
  }

  names(): string[] {
    return [...this.policies.keys()].sort();
  }
}
