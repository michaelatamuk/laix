# laix (TypeScript)

**LAIX — Live AI Experience — is the live decision runtime for AI agents and automations that act in the real world.**

This package contains the contracts, attention, action, the ten decision classes, Live Context,
streaming, outcome learning, bench, platform, stores, proposals, delivery, execution and records.
It mirrors the Python decision surface, including calibration, model learning and POMDP planning.

The source is split into `src/core` and `src/appkit`. The package exports one entry point, `laix`.

```ts
import { Layer } from "laix";

const layer = new Layer();
const decisions = layer.decide({
  subject: "one signal",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "k", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: null },
});
```

`Layer.decide` accepts either `signals` + `context` or `situation` + `options`, and returns the same
`Decision` shape for both. A policy plugin can be supplied with `new Layer({ policy })`, or
registered with `registerPolicy` and selected with `usePolicy`.

## Capabilities

| Area | Exports |
|---|---|
| Attention | `decide`, `score`, `costOfWaiting`, `OutcomeLog` |
| Action | `Layer`, `decideAction` |
| Planners | `UtilityPlanner`, `CommitmentPlanner`, `ExecutionRiskPlanner`, `HumanAttentionPlanner`, `MDPPlanner`, `POMDPPlanner`, `MdpModel`, `PomdpModel` |
| Engine and protocol | `LiveDecisionEngine`, `EnginePolicy`, `DecisionEngine`, `DecisionProblem`, `Plan`, `toDecision` |
| Simulation and bench | `Simulator`, `comparePlanners`, `runPlannerBench` |
| Policy packs | `ActivePerceptionPolicy`, `SafetyConstrainedPolicy`, `ReplanningPolicy`, `AllocationPolicy`, `NegotiationPolicy`, `PreferenceElicitationPolicy`, `VerificationPolicy`, `EscalationPolicy` |
| Authoring and target | `RulePolicy`, `Rule`, `TargetedPolicy`, `PlanningPolicy`, `GroupPolicy`, `ShadowPolicy`, `simulate` |
| Learned policy | `BanditPolicy`, `UCBBandit`, `Arm`, `rewardForLabel`, `CausalLedger`, `ModelLearner`, `CalibrationReport` |
| Live Context | `LiveContext`, `CallableDetector`, `Detector`, `Detection`, `PerceptionEvent` |
| Streaming | `StreamSession`, `StreamStats`, `ManualClock`, `TumblingWindow`, `WindowBatch`, `fromNdjson`, `fromSse`, `DeadLetterQueue` |
| Runtime | `DecisionRuntime`, `ExecutionBridge`, `ExperienceState`, `ResourceScheduler`, `Saga` |
| Execution | `ExecutionBridge` idempotency, unknown outcomes, reconciliation and `runSteps` |
| Platform | `Platform`, `InMemoryPlatform`, `SkillCall` |
| Stores | `StateStore`, `InMemoryStateStore`, `StreamCheckpointStore`, `InMemoryStreamCheckpointStore`, `FileStreamCheckpointStore`, `CommitmentStore`, `InMemoryCommitmentStore`, `FileCommitmentStore`, `OutcomeLedger`, `OutcomeStore` |
| Proposals | `createProposal`, `approveProposal`, `rejectProposal`, `applyProposal`, `undoProposal` |
| Delivery | `DeliveryPort`, `NullDelivery`, `DeliveryReceipt` |
| Evaluation | `compare`, `loadCases`, `Case`, `Report` |
| Bench | `runBench`, `suiteNames` |

The attention policy passes the same 24 decisions as Python. The bench runs the same 10 suites and
25 cases as Python.

## Test

```powershell
npm.cmd test
npm.cmd run bench
npm.cmd run conformance
npm.cmd run live-bench
```

`npm.cmd run conformance` compares every attention decision against
`packages/contracts/attention.v1.json` and exits non-zero on a mismatch.
`npm.cmd run bench` runs all decision classes.
`npm.cmd run live-bench` runs the shared 30-case test split and compares 210 action IDs with Python.
