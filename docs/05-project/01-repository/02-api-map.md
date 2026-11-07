# API map

One page for the public surface. Python and TypeScript export the same concepts. This is a
map by role, not a generated signature reference. The package `__all__` lists the core exports; the
app kit adds lazy exports and the bench runner adds its own `laix.appkit.bench` surface.

## Contract

| Name | Purpose |
|---|---|
| `DecisionRequest` | what is happening, the options and the limits |
| `Decision` | verb, reason, confidence, action, approval, target and trail |
| `ActionOption` | one action the host can offer |
| `Constraint` | risk, approval, safety, budget and other limits |
| `Situation` | beliefs, goals, observations and constraints |
| `Belief`, `Goal`, `Observation` | the situation's evidence and intent |
| `Intent`, `EvidenceRef` | what the action would do and what supports it |
| `ScoreBreakdown`, `Trace`, `ExecutionReceipt` | the score, the trail and the execution state |
| `Verb` | `wait`, `observe`, `guide`, `ask`, `act`, `verify`, `escalate` |
| `decide` | answer one request with the core |

## Commitments

| Name | Purpose |
|---|---|
| `Commitment` | one promised step with a due time, status, dependencies and priority |
| `CommitmentLedger` | the open promises for one task, with due and blocked queries |
| `CommitmentStore` | the persistence port for a ledger |
| `InMemoryCommitmentStore`, `FileCommitmentStore` | the built-in stores |
| `CommitmentPlanner` | the planner that scores fulfill, violate and create effects |

## Decision mechanisms

The layer rule is: **Planner** is a strategy, **Engine** is a composition, **Policy** is an
integration, **Learner** is learning. The protocol is `DecisionEngine`.

| Name | Purpose |
|---|---|
| `decide_attention`, `Signal`, `Context`, `Feedback` | rank signals and choose the attention verb |
| `AttentionDecision`, `AttentionBudget` | the attention result and its budget |
| `Policy` / `PolicyRegistry` | the smallest policy contract and a registry |
| `Rule`, `RulePolicy`, `TargetedPolicy` | authored rules and target modes |
| `EnginePolicy` | adapt a `DecisionEngine` to the policy interface |
| `PlanningPolicy` | act on the next actionable commitment |
| `GroupPolicy`, `ShadowPolicy`, `ShadowDifference` | sharing boundary and shadow comparison |
| `UtilityPlanner` | expected utility with hard limits and risk attitude |
| `ExecutionRiskPlanner` | irreversibility, unknown outcomes, approval and recovery |
| `HumanAttentionPlanner` | interruption, approval, escalation and a shared budget |
| `LiveDecisionEngine` | the composition engine: utility, commitments, execution risk and attention in one plan |
| `MDPPlanner`, `POMDPPlanner` | model-based planning over a host-supplied model |
| `Simulator`, `compare_planners` | run and compare planners |

## Perception and resources

| Name | Purpose |
|---|---|
| `Detection`, `Detector` | a perception result and the detector contract |
| `PerceptionEvent`, `PerceptionFrame` | the event and frame shapes |
| `LiveContext`, `CallableDetector` | host-driven perception loop |
| `Budget`, `ResourcePlan`, `ResourceScheduler`, `SensingOption` | resource admission and sensing |

## Learning and evaluation

| Name | Purpose |
|---|---|
| `Outcome`, `OutcomeLedger`, `OutcomeStore` | measured results and their store |
| `AttentionOutcome` | the attention-specific outcome shape |
| `UCBBandit`, `BanditPolicy`, `Arm` | reward-driven choice |
| `CalibrationReport`, `CalibrationBin` | confidence vs observed accuracy |
| `DecisionCalibrationReport`, `DecisionCalibrationSample`, `CalibratedPolicy` | decision accuracy and calibrated decisions |
| `CausalLedger`, `CausalObservation`, `CausalEffect` | treatment and control effects |
| `Case`, `Row`, `Report`, `compare_decisions` | case-based evaluation and parity |
| `ModelLearner`, `LearnedTransition` | learn a transition model and roll it back |

## App kit

| Name | Purpose |
|---|---|
| `Layer` | one decision with the optional runtime |
| `DecisionRuntime` | the app-kit decision loop |
| `StreamSession`, `DecisionTimeline` | event-time decisions, revisions and checkpoints |
| `StreamStats`, `DeadLetterQueue`, `TumblingWindow` | stream counters, failures and windows |
| `ExecutionBridge`, `Saga` | execution boundary, receipts, recovery and compensation |
| `ExperienceState`, `StateStore` | live state and its port |
| `DecisionRecord`, `create_record`, `approve_record`, `reject_record`, `mark_executed`, `verify_record` | the audit lifecycle |
| `Proposal`, `approve_proposal`, `reject_proposal`, `apply_proposal`, `undo_proposal` | the proposal lifecycle |
| `ApprovalRequest`, `ApprovalDecision` | approval hand-off |
| `Platform`, `InMemoryPlatform`, `SkillCall` | host skills, events and approvals |
| `DeliveryPort`, `DeliveryReceipt`, `NullDelivery` | delivery boundary and receipt |
| `prometheus`, `run_stream_bench` | metrics and stream bench |

## Proof

| Name | Purpose |
|---|---|
| `run_live_bench` / `runLiveBench` | compare training-free planners on the seven-case demo |
| `default_cases`, `default_planners` | the demo case set and planner set |
| `LiveBenchReport`, `LiveBenchRow`, `PlannerMetrics` | the live-bench report |
| `run_stream_bench`, `StreamBenchResult` | stream throughput and counters |
| `prometheus`, `StreamStats` | Prometheus counters from a stream |
| `BenchCase`, `BenchReport`, `BenchRow`, `Suite`, `run_bench`, `suite_names`, `run_planner_bench` | LAIX-Bench, from `laix.appkit.bench` |

The bench runner classes are exported from `laix.appkit.bench`. The rest are in `laix`.

## Reading the API

- Start with `DecisionRequest` and `Decision`; they are the contract.
- Use `decide` for the core, or `Layer` when you want the app kit.
- Use `EnginePolicy` to put a planner or an engine behind the policy contract.
- Use `ExecutionBridge` and `DecisionRecord` when the decision changes the world.
- The app kit is optional; importing `laix` does not load it until first use.
