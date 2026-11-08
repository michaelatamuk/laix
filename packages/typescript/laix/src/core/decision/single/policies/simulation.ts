import type { Decision, DecisionRequest } from "../../../contracts.ts";

export interface PolicyLike {
  decide(request: DecisionRequest): Decision[];
}

function signature(decisions: Decision[]): string {
  return decisions
    .map((item) => `${item.verb}\u0000${item.actionId ?? ""}\u0000${item.reasonCode}`)
    .join("\u0001");
}

export function simulate(
  policy: PolicyLike,
  requests: DecisionRequest[],
): Decision[][] {
  return requests.map((request) => [...policy.decide(request)]);
}

export interface ShadowDifference {
  request: DecisionRequest;
  primary: Decision[];
  shadow: Decision[];
}

export class ShadowPolicy {
  readonly name: string;
  readonly primary: PolicyLike;
  readonly shadow: PolicyLike;
  differences: ShadowDifference[] = [];

  constructor(primary: PolicyLike, shadow: PolicyLike, name = "shadow.v1") {
    this.primary = primary;
    this.shadow = shadow;
    this.name = name;
  }

  decide(request: DecisionRequest): Decision[] {
    const primary = [...this.primary.decide(request)];
    const shadow = [...this.shadow.decide(request)];
    if (signature(primary) !== signature(shadow)) {
      this.differences.push({ request, primary, shadow });
    }
    return primary;
  }
}
