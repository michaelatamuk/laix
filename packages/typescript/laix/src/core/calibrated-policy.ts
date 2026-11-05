import type { Decision, DecisionRequest } from "./contracts.ts";
import { calibrateDecision } from "./calibrate-decision.ts";
import type { DecisionCalibrationReport } from "./decision-calibration-report.ts";
import type { Policy } from "./policies/registry.ts";

export class CalibratedPolicy implements Policy {
  readonly name: string;
  readonly policy: Policy;
  readonly report: DecisionCalibrationReport;

  constructor(
    policy: Policy,
    report: DecisionCalibrationReport,
    name?: string,
  ) {
    this.policy = policy;
    this.report = report;
    this.name = name ?? `${policy.name}.calibrated`;
  }

  decide(request: DecisionRequest): Decision[] {
    return this.policy
      .decide(request)
      .map((decision) => calibrateDecision(decision, this.report));
  }
}
