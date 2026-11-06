# Changelog

## Unreleased

### Added

- **Live decision benchmark.** A 120-case corpus across promise, execution, attention, timing,
  conflict and plain categories, with dev/test/adversarial splits, JSON Schema validation,
  bootstrap confidence intervals, paired significance tests and a hand-built glue baseline.
- **Novelty evidence.** Prior-art matrix, formal model and invariants, claim–evidence map,
  EU Product Liability mapping, paper draft and validation harness.
- **Validation harness.** Incident ingestion with PII stripping and a comparison script for
  recorded human decisions.
- **TypeScript live-bench parity.** The TypeScript planners run the same 30-case test split and
  match Python on all 210 action IDs.
- **External comparison harness.** A LangGraph adapter runs the same decision engine in a state
  graph and reports operational overhead; Temporal, PagerDuty and Camunda remain documented-only.
- **Built-in decision engines.** `UtilityEngine` with hard limits and risk attitude, `MDPEngine`
  with value iteration, and `POMDPEngine` with belief update and finite-horizon planning.
- **Engine proof.** `Simulator`, seeded scenarios, `compare_engines` with reward and optimality gap,
  `CalibrationReport` and `ModelLearner` with rollback.
- **Python planning and execution depth.** `CommitmentStore` with in-memory and file stores,
  `PlanningPolicy` skipping blocked commitments, and `ExecutionBridge.run_steps` with
  receipt-linked compensation.
- **Causal depth.** `add_outcome`, `from_outcomes`, standard errors, 95% intervals and
  `effect_by_context`.
- **Engine and stream depth.** `ModelLearner.to_mdp_model`, seeded stochastic MDP rollouts,
  `compare_pomdp_to_mdp`, a Python `--engines` bench, NDJSON/SSE error policies and checkpoint
  stream-id validation.
- **Privacy depth.** `GroupPolicy` masks nested attributes, intent arguments, alternatives and
  evidence, and can replace the rationale and undo hint.
- **Stream depth.** `DeadLetterQueue` retains malformed source frames; NDJSON and SSE accept sync
  or async lines.
- **Calibration depth.** Optional Laplace smoothing for small bins.
- **TypeScript parity for the 0.9.0 depth work.** Checkpoint stores, NDJSON/SSE sources,
  `CausalLedger`, commitments and `PlanningPolicy`, `GroupPolicy`, `ShadowPolicy` / `simulate` and
  `Saga`.
- **TypeScript engine surface.** `UtilityEngine`, `MDPEngine`, `Simulator` and `compareEngines`.
- **Examples** for checkpoints, sources, causal attribution, planning, group/shadow, sagas,
  calibration, model learning, utility, MDP and POMDP.

### Changed

- Repositioned the README around the decision-runtime category, restored the training-free property to the opening, and aligned the docs and package one-liners. No API changes.
- Reordered the repository for role-based grouping: `benchmarks/live/v1/` (versioned corpus), `benchmarks/compare/adapters/` (per-system adapters), `data/{incident-replay,vignette-study/v1}/`, `results/live-decision-benchmark/`, `scripts/ci/`, `scripts/novelty/{bench,analysis,compare,incident-replay,vignette-study,shared}/` and `docs/06-research/` (the research dossier moved out of `05-project`). Public APIs and package layout are unchanged.
- Added `to_decision` / `toDecision` as the one plan-to-decision conversion.
- TypeScript now mirrors the Python calibration, model-learning and POMDP surface.

### Tooling

- CI runs `ruff check` for Python and `tsc --noEmit` for TypeScript; TypeScript uses a committed
  `package-lock.json`.
- CI validates the live-bench cases and runs the benchmark, paired analysis and ablations through
  `scripts/novelty/reproduce.sh`.

## 0.9.0 — 2026-11-05

### Added

- **Streaming decisions.** `StreamSession`, `TumblingWindow` and the stream fields on
  `Decision` / `DecisionRequest`: event time, dedupe, cooldown, hysteresis, budget,
  backpressure, revisions, deadlines, checkpoints and traces. Queue/sync sources,
  Prometheus counters and a stream bench are included.
- **Engine contract.** `DecisionEngine`, `DecisionProblem`, `Plan` and `EnginePolicy`
  so JEV, an optimizer, a POMDP library or a LAIX planner can sit behind one policy.
- **Execution integrity.** Idempotency keys, `duplicate` receipts, `unknown` outcomes
  and reconciliation in `ExecutionBridge`.
- **Policy authoring and target.** `RulePolicy` with declarative rules, and
  `TargetedPolicy` with `one` / `some` / `all` / `peer` / `gather` targets.
- **TypeScript parity** for the streaming runtime, engine policy, execution integrity,
  target fields, rule policies and targeted policies.
- **Durable checkpoints and stream sources.** In-memory and file checkpoint stores; NDJSON and SSE
  sources.
- **Causal attribution.** `CausalLedger` estimates a treatment effect with difference in means or
  inverse propensity weighting.
- **Planning and commitments.** `Commitment`, `CommitmentLedger` and `PlanningPolicy`.
- **Group and shadow policies.** `GroupPolicy` masks private attributes; `ShadowPolicy` records
  disagreements without changing the primary decision.
- **Execution sagas.** `Saga` compensates completed steps in reverse when a later step fails.
- **Docs and examples** for streaming, the engine contract, execution integrity and
  the authoring surface.

### Changed

- `ExecutionReceipt` gained `idempotency_key` and the `unknown` / `duplicate` statuses.
- `Decision` and `DecisionRequest` gained `target` and `recipients`.
