# API map

One page for the public surface. Python and TypeScript export the same concepts.

## Contract

| Name | Purpose |
|---|---|
| `DecisionRequest` | what is happening, the options and the limits |
| `Decision` | verb, reason, confidence, action, approval, target and trail |
| `ActionOption` | one action the host can offer |
| `Constraint` | risk, approval, safety, budget and other limits |
| `Situation` | beliefs, goals, observations and constraints |
| `decide` | answer one request with the core |

## Decision mechanisms

| Name | Purpose |
|---|---|
| `decide_attention` | rank signals and choose the attention verb |
| `Policy` / `PolicyRegistry` | the smallest policy contract and a registry |
| `RulePolicy`, `TargetedPolicy` | authored rules and target modes |
| `EnginePolicy` | wrap a planner as a policy |
| `UtilityEngine` | expected utility with hard limits and risk attitude |
| `CommitmentAwareEngine` | promises, due times, dependencies and priority |
| `ExecutionAwareEngine` | irreversibility, unknown outcomes, approval and recovery |
| `AttentionAwareEngine` | interruption, approval, escalation and a shared budget |
| `LiveDecisionEngine` | commitments, execution risk and attention in one plan |
| `MDPEngine`, `POMDPEngine` | model-based planning over a host-supplied model |

## Learning and evaluation

| Name | Purpose |
|---|---|
| `Outcome`, `OutcomeLedger` | measured results and their store |
| `UCBBandit`, `BanditPolicy` | reward-driven choice |
| `CalibrationReport` | confidence vs observed accuracy |
| `DecisionCalibrationReport`, `CalibratedPolicy` | decision accuracy and calibrated decisions |
| `CausalLedger` | treatment and control effects |
| `Simulator`, `compare_engines` | run and compare planners |

## App kit

| Name | Purpose |
|---|---|
| `Layer` | one decision with the optional runtime |
| `StreamSession` | event-time decisions, revisions and checkpoints |
| `DecisionTimeline` | revision, predecessor and event-time semantics |
| `ExecutionBridge`, `Saga` | execution boundary, receipts and recovery |
| `ExperienceState`, `StateStore` | live state and its port |
| `Platform`, `DeliveryPort` | host skills, approvals and delivery |
| `LiveContext` | detectors and perception frames |

## Proof

| Name | Purpose |
|---|---|
| `run_live_bench` / `runLiveBench` | compare training-free planners |
| `run_stream_bench` | stream throughput and counters |
| `Bench`, `Metrics` | LAIX-Bench and Prometheus counters |
