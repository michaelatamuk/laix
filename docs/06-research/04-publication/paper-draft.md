# One decision contract for live AI: commitments, execution risk and attention

**Status: draft. Not submittable.** Real-world validation and external review are still pending.
Numbers below come from the frozen synthetic test split and `results/live-decision-benchmark/`.

## Abstract

Live AI systems must decide whether to wait, observe, guide, ask, act, verify or escalate before
the moment passes. Existing tools cover orchestration, durable workflows, alerting or planning
separately. We present LAIX, a training-free live decision runtime that places commitments, execution risk
and human attention budget into one decision contract with the verb, score, reason code and audit
trail. On a 120-case synthetic corpus, `LiveCompositePlanner` is 30/30 on the frozen test split and
wins every conflict case. Against a hand-built glue baseline it is +6.7 percentage points
(95% CI 0.0–0.167, McNemar p = 0.48), so the integration advantage over competent glue code is not
yet significant. We report the result honestly and define the validation needed to establish it.

## 1. Introduction

A live experience is always in the loop. The host knows the domain; the live decision runtime must answer
one question: what matters now, and what should the experience do about it?

The contribution is a decision contract and a composition:

- one object carries the chosen verb, action, confidence, score, reason code and alternatives;
- commitments, execution risk and attention are first-class terms in that object;
- the decision is deterministic, training-free and replayable;
- the host keeps execution, storage and delivery.

`LiveCompositePlanner` is the proof object.

## 2. Related work

Use `../01-positioning/comparators.md` as the source. The closest categories are:

- agent orchestration: LangGraph, AutoGen, CrewAI and Semantic Kernel;
- durable execution: Temporal, Airflow, Prefect and Conductor;
- alerting and on-call: PagerDuty and Opsgenie;
- commitment protocols: FIPA ACL and commitment-based multi-agent systems;
- planning: MDP/POMDP solvers and HTN/PDDL planners;
- execution safety: sagas and compensation;
- calibration: reliability diagrams, Brier score and expected calibration error.

The documented comparison found no system that carries all ten capabilities in one decision object.
That is a capability gap; measuring it is the next step.

## 3. Decision contract and formal model

Summarise `../01-positioning/formal-model.md`:

- `PlannerInput`: subject, time, situation, options, signals, context and attributes.
- `ActionOption`: benefit, cost, risk, interruption, latency, reversibility, approval and params.
- `Commitment`: id, subject, due time, status, priority and dependencies.
- `HumanAttentionBudget`: total, spent and remaining.
- `PlannerResult`: verb, action, confidence, score, reason code, rationale and alternatives.
- `Decision`: the public shape produced by `PlannerPolicy`.

The integrated score is:

```text
total(o) = utility(o) + commitment(o) + execution(o) + attention(o)
```

with hard feasibility gates applied before scoring. Invariants I1–I10 are in `../01-positioning/formal-model.md` and
are covered by `tests/core/test_invariants.py`.

## 4. Integrated live planning

`LiveCompositePlanner` adds:

- the utility term from `UtilityPlanner`;
- a commitment term that rewards keeping promises and penalises violations;
- an execution term for irreversibility, unknown outcomes, approval and recovery;
- an attention term for interruption, approval, escalation and exhausted budgets.

The planner is deterministic and returns the same `PlannerResult` shape as every other planner.

## 5. Execution, audit and revision

The host executes. LAIX provides:

- a receipt state machine with idempotency, approval, cancellation, undo, unknown outcomes and
  reconciliation;
- an append-only trace;
- a timeline with revision monotonicity and event-time rules;
- a decision record with `decision_id`, `trace_id`, `policy_version` and `created_at`.

`eu-liability.md` maps these fields to the questions raised by EU Product Liability Directive
2024/2853.

## 6. Calibration and outcome learning

The layer can:

- bin predictions and compare confidence with observed accuracy;
- calibrate decision confidence, not only class probabilities;
- use UCB for arm selection;
- estimate treatment effects with difference in means or inverse propensity weighting;
- learn a small transition model with rollback.

Evaluation on real outcomes is the next step for the calibration and causal paths.

## 7. Implementation and parity

- Python: `packages/python/laix`
- TypeScript: `packages/typescript/laix`
- Shared conformance cases: 24/24 signal-attention decisions
- Live-bench action parity: 210/210 Python/TypeScript decisions agree on the test split
- LangGraph operational adapter: 120 decisions, 0 interrupts, 6-7 ms mean, 110 glue lines
- Python invariant tests: 17/17
- TypeScript tests: 202
- CI: Python 3.11/3.13, Node 22/24, docs links and the live-bench reproduction

## 8. Evaluation

### 8.1 Corpus

120 synthetic cases:

| Split | Cases |
|---|---:|
| dev | 72 |
| test | 30 |
| adversarial | 18 |

Categories: promise 20, execution 20, attention 20, timing 15, conflict 25, plain 20.
The test split is frozen at dataset version 1.0.0.

### 8.2 Main result (test split, 30 cases)

| Component | Accuracy | 95% CI | Promise keeping | Irreversible | Budget violations |
|---|---:|---:|---:|---:|---:|
| First-option baseline | 70.00% | 0.53-0.87 | 58.33% | 13.33% | 77.78% |
| Highest-benefit baseline | 23.33% | 0.10-0.40 | 0.00% | 23.33% | 70.00% |
| UtilityPlanner | 30.00% | 0.13–0.47 | 0.00% | 23.33% | 70.00% |
| CommitmentPlanner | 70.00% | 0.53–0.87 | 100.00% | 13.33% | 57.14% |
| ExecutionRiskPlanner | 50.00% | 0.33–0.67 | 8.33% | 6.67% | 62.50% |
| HumanAttentionPlanner | 53.33% | 0.37–0.70 | 25.00% | 16.67% | 0.00% |
| Glue baseline | 93.33% | 0.83–1.00 | 100.00% | 0.00% | 0.00% |
| **LiveCompositePlanner** | **100.00%** | **1.00–1.00** | **100.00%** | **0.00%** | **0.00%** |

Conflict cases: `LiveCompositePlanner` and the glue baseline are 100%; the best single-concern
planner is `CommitmentPlanner` at 83.3%.

### 8.3 Ablations (test split)

| Variant | Accuracy | Promise keeping | Irreversible | Budget violations |
|---|---:|---:|---:|---:|
| full | 100.00% | 100.00% | 0.00% | 0.00% |
| equal weights | 100.00% | 100.00% | 0.00% | 0.00% |
| no attention | 96.67% | 100.00% | 0.00% | 0.00% |
| no feasibility gates | 93.33% | 100.00% | 0.00% | 0.00% |
| no execution | 83.33% | 100.00% | 10.00% | 0.00% |
| no commitment | 70.00% | 25.00% | 6.67% | 0.00% |
| utility only | 30.00% | 0.00% | 23.33% | 70.00% |

Removing commitments costs 30 accuracy points, removing execution risk costs 16.7 and removing
attention costs 3.3. The composition is doing real work.

### 8.4 Paired significance

| Comparator | Accuracy delta | 95% CI | McNemar p | Cohen's h |
|---|---:|---:|---:|---:|
| Highest-benefit baseline | +76.7 pp | 0.600–0.900 | <0.001 | 2.133 |
| UtilityPlanner | +70.0 pp | 0.533–0.867 | <0.001 | 1.982 |
| ExecutionRiskPlanner | +50.0 pp | 0.333–0.667 | <0.001 | 1.571 |
| HumanAttentionPlanner | +46.7 pp | 0.300–0.633 | <0.001 | 1.504 |
| CommitmentPlanner | +30.0 pp | 0.133–0.467 | 0.008 | 1.159 |
| First-option baseline | +30.0 pp | 0.133–0.467 | 0.008 | 1.159 |
| **Glue baseline** | **+6.7 pp** | **0.000–0.167** | **0.480** | **0.522** |

The result against glue is the key limitation: the confidence interval includes zero. The synthetic
corpus is too easy, and the next section is the missing evidence.

### 8.5 Failure analysis

`LiveCompositePlanner` made zero mistakes on the 30 test cases and zero on the 18 adversarial cases. That is a warning. The corpus does not yet contain ambiguous trade-offs, noisy outcomes,
multi-step dependencies, long-tail incidents or host-specific recovery behaviour. A benchmark with
no failures cannot support a strong generalisation claim.

## 9. Real-world validation (pending)

Choose one from `../03-validation/plan.md`:

- deployment or pilot;
- incident or support replay;
- user study.

The harness is ready:

- `scripts/novelty/incident-replay/ingest_incidents.py` anonymises a JSONL export;
- `scripts/novelty/incident-replay/analyze_incident_replay.py` compares LAIX, glue and utility against recorded human decisions;
- `data/incident-replay/README.md` defines the format and privacy rules.

No real data has been collected. Until it is, the novelty claim is a synthetic systems claim plus a
documented capability gap.

## 10. Threats to validity

- synthetic cases may not represent real traffic;
- the benchmark may encode the authors' assumptions;
- `LiveCompositePlanner` may win because the baselines are weak;
- the glue baseline narrows the advantage to +6.7 pp and the result is not significant;
- a single domain limits generality;
- deterministic cases hide variance;
- the attention model is a simplification of human workload;
- calibration needs real outcomes;
- the framework is model-free and does not cover learned policies;
- author-run evaluation creates bias;
- parity tests prove consistency, not correctness.

## 11. Conclusion

LAIX defines one decision contract for commitments, execution risk and attention, and implements it
with deterministic, training-free planners, audit and parity. The synthetic evidence shows a large
advantage over single-concern planners and a smaller, not-yet-significant advantage over competent
glue code. The next step is real-world validation, not more synthetic cases.

## Appendix: reproducibility

```bash
bash scripts/novelty/reproduce.sh
```

Files:

- `benchmarks/live/v1/` — 120 cases and schema;
- `results/live-decision-benchmark/metrics/summary.json` — baseline metrics;
- `results/live-decision-benchmark/metrics/significance.json` — paired tests and categories;
- `results/live-decision-benchmark/ablations/results.json` — ablation results;
- `results/live-decision-benchmark/raw/decisions.jsonl` — per-case rows.
