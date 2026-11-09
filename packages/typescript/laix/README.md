# laix (TypeScript)

**LAIX — Live AI Experience — is the live decision layer for AI agents that act in the real world.**

This package contains the contracts, signal attention, action, the ten decision classes, Live Context,
streaming, outcome learning, bench, platform, stores, proposals, delivery, execution and records.
It mirrors the Python decision surface, including calibration, model learning and POMDP planning.

The source is split into `src/core` and `src/appkit`. The package exports one entry point, `laix`.

```ts
import { DecisionClient } from "laix";

const layer = new DecisionClient();
const decisions = layer.decide({
  subject: "one signal",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "k", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: null },
});
```

`DecisionClient.decide` accepts either `signals` + `context` or `situation` + `options`, and returns the same
`Decision` shape for both. A policy plugin can be supplied with `new DecisionClient({ policy })`, or
registered with `registerPolicy` and selected with `usePolicy`.

## Capabilities

| Area | Exports |
|---|---|
| Signal attention | `decideSignalAttention`, `score`, `costOfWaiting`, `SignalAttentionLog` |
| Action | `DecisionClient`, `decideAction` |
| Planners | `UtilityPlanner`, `CommitmentPlanner`, `ExecutionRiskPlanner`, `HumanAttentionPlanner`, `MDPPlanner`, `POMDPPlanner`, `MdpModel`, `PomdpModel` |
| Composite planner and protocol | `LiveCompositePlanner`, `PlannerPolicy`, `Planner`, `PlannerInput`, `PlannerResult`, `toDecision` |
| Algorithm prototypes | `CAVODPlanner`, `AttentionScheduler`, `WhittleScheduler`, `repairContinuity`, `counterfactualAttribution`, `counterfactualSearch` |
| Simulation and bench | `Simulator`, `comparePlanners`, `runPlannerBench` |
| DecisionPolicy packs | `ActivePerceptionPolicy`, `SafetyConstrainedPolicy`, `ReplanningPolicy`, `AllocationPolicy`, `NegotiationPolicy`, `PreferenceElicitationPolicy`, `VerificationPolicy`, `EscalationPolicy` |
| Authoring and target | `RulePolicy`, `Rule`, `TargetedPolicy`, `PlanningPolicy`, `GroupPolicy`, `ShadowPolicy`, `simulate` |
| Learned policy | `BanditPolicy`, `UCBBandit`, `Arm`, `rewardForLabel`, `CausalLedger`, `ModelLearner`, `CalibrationReport` |
| Live Context | `LiveContext`, `CallableDetector`, `Detector`, `Detection`, `PerceptionEvent` |
| Streaming | `StreamSession`, `StreamStats`, `ManualClock`, `TumblingWindow`, `WindowBatch`, `fromNdjson`, `fromSse`, `DeadLetterQueue` |
| Runtime | `DecisionRuntime`, `ExecutionBridge` (sync, async, retries, timeouts), `ExperienceState`, `ResourceScheduler`, `Saga`, `RetryOptions`, `AsyncHandler` |
| Execution | `ExecutionBridge` idempotency, unknown outcomes, reconciliation and `runSteps` |
| Platform | `Platform`, `InMemoryPlatform`, `SkillCall` |
| Stores | `StateStore`, `InMemoryStateStore`, `FileStateStore`, `StreamCheckpointStore`, `InMemoryStreamCheckpointStore`, `FileStreamCheckpointStore`, `CommitmentStore`, `InMemoryCommitmentStore`, `FileCommitmentStore`, `OutcomeLedger`, `OutcomeStore`, `FileOutcomeStore` |
| Observability | `decisionAttributes`, `AttributeValue` |
| Proposals | `createProposal`, `approveProposal`, `rejectProposal`, `applyProposal`, `undoProposal` |
| Delivery | `DeliveryPort`, `NullDelivery`, `DeliveryReceipt` |
| Evaluation | `compare`, `loadCases`, `Case`, `Report` |
| Bench | `runBench`, `suiteNames` |

The signal-attention policy passes the same 24 decisions as Python. The bench runs the same 10 suites and
25 cases as Python.

## Build

```powershell
npm.cmd run build
npm.cmd pack
```

The build writes ESM JavaScript to `dist/`. The package keeps the curated public declarations in
`types.d.ts`, and `prepare` rebuilds `dist/` before a local install or package tarball.

## Test

```powershell
npm.cmd test
npm.cmd run bench
npm.cmd run conformance
npm.cmd run live-bench
```

`npm.cmd run conformance` compares every signal-attention decision against
`packages/contracts/signal-attention.v1.json` and exits non-zero on a mismatch.
`npm.cmd run bench` runs all decision classes.
`npm.cmd run live-bench` runs the shared 30-case test split and compares 210 action IDs with Python.
