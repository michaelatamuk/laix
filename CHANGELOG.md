# Changelog

## Unreleased

### Added

- **File-backed stores.** `FileStateStore` writes one JSON snapshot per key, and `FileOutcomeStore`
  extends `OutcomeLedger` with a JSON file after every `add` or `record`. TypeScript mirrors both.
- **OpenTelemetry attributes.** `decision_attributes` / `decisionAttributes` map a decision onto
  stable `laix.*` span attributes without adding an SDK dependency.
- **Execution retries.** `RetryPolicy` and TypeScript `RetryOptions` retry a failed handler with
  capped exponential backoff and record the attempt count in the receipt detail.
- **Async execution.** `register_async` / `registerAsync`, `execute_async` / `executeAsync`,
  `run_steps_async` / `runStepsAsync` and hard timeouts. A timeout returns an `unknown` receipt
  because the effect may have happened.
- **Developer CLI.** `laix explain` and `laix lint` inspect a decision or decision-record JSON file
  without importing the host app.
- **LangGraph guide.** A production-shaped decision node, approval interrupt, checkpointer resume
  and execution receipt, with the boundary between LangGraph and LAIX.
- **Validation template.** A pre-registration page for external runs, with the metrics, analysis
  plan, threats and replication rules.
- **Community templates.** Bug and feature issue forms, a pull request template and a documentation
  contact link.

## 0.10.0 - 2026-11-08

### Breaking

- **Planner vocabulary.** The planner contract is now `Planner` (`DecisionEngine`), `PlannerInput`
  (`DecisionProblem`), `PlannerResult` (`Plan`) and `PlannerPolicy` (`EnginePolicy`).
  `LiveDecisionEngine` is now `LiveCompositePlanner`.
- **Policy vocabulary.** `Policy` is now `DecisionPolicy`, with `DecisionPolicyRegistry` and
  `DecisionPolicyError`. `Layer` is now `DecisionClient`.
- **Attention vocabulary.** `decide_attention` is now `decide_signal_attention`. The signal-side
  records are `SignalContext`, `SignalFeedback`, `SignalAttentionDecision`,
  `SignalAttentionOutcome` and `SignalAttentionLog`. The planning-side records are
  `HumanAttentionBudget`, `HumanAttentionEffect`, `HumanAttentionScore` and
  `HumanAttentionWeights`.
- **File and vector names.** The contract, live planner, policy, app-kit client, signal, human
  attention and outcome paths moved with the names. The attention vectors are now
  `signal-attention.v1.json` and `signal-attention-bench.v1.json`.
- **Data identifiers.** Benchmark keys stay unchanged. Human-attention attributes and reason codes
  use the `human_attention_*` prefix.
- Renamed `LiveScore` to `CompositeScore`, `EngineScore` to `PlannerBenchmarkRow`,
  `compare_engines` / `compareEngines` to `compare_planners` / `comparePlanners`, and the
  `*Engine` planners to `*Planner`.
- JSON keys and reason codes for the benchmark stay unchanged: `live`, `glue`, `commitment`,
  `execution`, `attention`, `utility`, `first`, `benefit` and `live_decision`.
- No compatibility aliases are provided; see the
  [migration guide](docs/05-project/03-release/02-migration.md).

### Added

- **Sequence planning.** `CABBPlanner` for exact finite-horizon commitment- and attention-constrained
  branch and bound, `RolloutPlanner` for a bounded greedy rollout and `ReplanPlanner` for rebuilding
  the remaining chain after an executed prefix, with Python/TypeScript tests, examples and a smoke
  benchmark.
- **Algorithm prototypes.** `CAVODPlanner` for one-step value of decision and optional
  belief-state future value, `AttentionScheduler` and `WhittleScheduler` for attention-aware
  decision scheduling, `repair_continuity` for greedy or exact continuity repair and
  `counterfactual_attribution` plus `counterfactual_search` for decision explanations, with
  Python/TypeScript tests, examples and a research smoke benchmark.
- **Live decision benchmark.** A 120-case corpus across promise, execution, attention, timing,
  conflict and plain categories, with dev/test/adversarial splits, JSON Schema validation,
  bootstrap confidence intervals, paired significance tests and a hand-built glue baseline.
- **Novelty evidence.** Prior-art matrix, formal model and invariants, claim–evidence map,
  EU Product Liability mapping, paper draft and validation harness.
- **Validation harness.** Incident ingestion with PII stripping and a comparison script for
  recorded human decisions.
- **TypeScript live-bench parity.** The TypeScript planners run the same 30-case test split and
  match Python on all 210 action IDs.
- **External comparison harness.** A LangGraph adapter runs the same composite planner in a state
  graph and reports operational overhead; Temporal, PagerDuty and Camunda remain documented-only.
- **Built-in planners.** `UtilityPlanner` with hard limits and risk attitude, `MDPPlanner`
  with value iteration, and `POMDPPlanner` with belief update and finite-horizon planning.
- **Planner proof.** `Simulator`, seeded scenarios, `compare_planners` with reward and optimality
  gap, `CalibrationReport` and `ModelLearner` with rollback.
- **Python planning and execution depth.** `CommitmentStore` with in-memory and file stores,
  `PlanningPolicy` skipping blocked commitments, and `ExecutionBridge.run_steps` with
  receipt-linked compensation.
- **Causal depth.** `add_outcome`, `from_outcomes`, standard errors, 95% intervals and
  `effect_by_context`.
- **Planner and stream depth.** `ModelLearner.to_mdp_model`, seeded stochastic MDP rollouts,
  `compare_pomdp_to_mdp`, a Python `--planners` bench, NDJSON/SSE error policies and checkpoint
  stream-id validation.
- **Privacy depth.** `GroupPolicy` masks nested attributes, intent arguments, alternatives and
  evidence, and can replace the rationale and undo hint.
- **Stream depth.** `DeadLetterQueue` retains malformed source frames; NDJSON and SSE accept sync
  or async lines.
- **Calibration depth.** Optional Laplace smoothing for small bins.
- **TypeScript parity for the 0.9.0 depth work.** Checkpoint stores, NDJSON/SSE sources,
  `CausalLedger`, commitments and `PlanningPolicy`, `GroupPolicy`, `ShadowPolicy` / `simulate` and
  `Saga`.
- **TypeScript planner surface.** `UtilityPlanner`, `MDPPlanner`, `Simulator` and
  `comparePlanners`.
- **Distribution.** The TypeScript package builds ESM JavaScript to `dist/` and keeps the curated
  `types.d.ts`; `prepare` rebuilds it. The Python package ships `py.typed` and PEP 639 metadata.
  A manual publish workflow targets PyPI and npm.
- **Examples** for checkpoints, sources, causal attribution, planning, group/shadow, sagas,
  calibration, model learning, utility, MDP and POMDP.
- **Brand and visuals.** Logo, banner, avatar, a vector how-it-works loop, generated core-layer and
  app-kit-stage SVGs, benchmark and ablation charts, and a reproducible asset renderer in
  `scripts/docs/`.
- **Project docs.** Contributing, security policy, code of conduct, support, deployment,
  troubleshooting, migration, commitments, decision continuity and an expanded API map.
- **Decision continuity.** A README section, a dedicated core page and a sequence-benchmark
  design note for commitments, budget, approvals, revisions and outcomes carried across decisions.

### Changed

- Layered `core` by role: records and state now live under `domain/` (`decisions`, `commitments`,
  `outcomes`, `perception`), processing under `engines/` (`decision`, `sensing`, `learning`,
  `evaluation`), and interfaces under `contract/`. The engine folders keep the decision-shape
  grouping (`single`, `sequence`, `fleet`, `history`, `explain`). CA-VOD is split into planner,
  weights and score files. Public class names are unchanged; only the import paths moved.
- Repositioned the README around the live decision-runtime category, restored the training-free property to the opening, and aligned the docs and package one-liners. No API changes.
- Tightened the README hero, contents and Why section, replaced the slide-style benchmark and ablation images with matplotlib charts generated from the committed result JSON, and replaced the architecture slide with a light vector loop. Removed the generated demo animation; the code examples carry the demo until a real recording exists.
- Restructured the claim–evidence map into headline, safety, contract, open-claims and evidence-index tables.
- Split the README results into outcome, ablation and verification tables, with the glue baseline shown as the best comparator.
- Standardised docs on full engine class names (`LiveCompositePlanner`, `UtilityPlanner`,
  `CommitmentPlanner`, `ExecutionRiskPlanner`, `HumanAttentionPlanner`). Short keys stay in JSON
  and CLI output and are documented in `results/live-decision-benchmark/README.md`.
- Replaced the two block-beta overview diagrams with generated SVG assets, and corrected the
  signal-gate, value-iteration, continuity-sequence, planner-sequence and composite diagrams.
- Added a README comparison table, a "Can they be compared?" protocol, and comparison links that
  distinguish decision models such as JEV from the LAIX decision runtime.
- Trimmed the README verification matrix and documentation index; the full check matrix stays in
  Testing and the full page map stays in the docs index.
- Moved the JEV comparison into its own README section and tightened the capability-to-rationale
  flow.
- Moved the README ablation chart to the benchmark page and kept a compact ablation table in the
  README.
- Made the benchmark chart self-contained with accuracy, confidence-interval, conflict-subset and
  significance notes.
- Added an external-benchmark landscape and a component evaluation protocol (`τ-bench` first,
  `ITBench` second); no external result is claimed yet.
- Ran Sev1-Bench on all 20 scenarios: baseline 0.800, LAIX guardrail 0.800, LAIX chooser 0.745
  with one forbidden action. The chooser regressed on multi-incident triage and large-tool-result;
  the guardrail preserved the model's answer. Results and harness are in
  `results/external/sev1-bench/`.
- Repeated Sev1-Bench with DeepSeek V4 Pro on 16 successful scenarios: baseline 0.656, guardrail
  0.656, chooser 0.637. The guardrail removed the one forbidden recommendation without losing
  score.
- Added a decision-continuity benchmark v0: 12 episodes, 60 decisions. Stateful
  `LiveCompositePlanner` succeeded on 100% of episodes; a stateless `UtilityPlanner` on 0% with 36
  continuity errors. This is a synthetic mechanism test, not external validation.
- Ran the τ-bench retail baseline with DeepSeek V4 Flash: 9/10 tasks, `pass^1 = 0.90`. The LAIX
  policy adapter is not implemented; τ-bench scores full-agent tool use, not the runtime lifecycle.
- Added a τ-bench LAIX guardrail adapter and documented that task 0 failed on user-instruction
  drift, not a policy violation.
- Ran the τ-bench retail slice with the LAIX guardrail: **10/10** vs 9/10 baseline. Single trial,
  10 tasks; a positive signal, not a significance claim.
- Documented the power needed for the glue comparison: about 90-120 new held-out cases at the
  current effect size, run once on a pre-registered set.
- Added a secondary adversarial-split check: 18/18 vs 16/18, combined exact McNemar p = 0.125.
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
- **Engine contract.** `Planner`, `PlannerInput`, `PlannerResult` and `PlannerPolicy`
  so JEV, an optimizer, a POMDP library or a LAIX planner can sit behind one policy.
- **Execution integrity.** Idempotency keys, `duplicate` receipts, `unknown` outcomes
  and reconciliation in `ExecutionBridge`.
- **DecisionPolicy authoring and target.** `RulePolicy` with declarative rules, and
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
