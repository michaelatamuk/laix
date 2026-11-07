# Research and evidence

This is the working plan for establishing the novelty claim. It turns the claim that LAIX is novel
into a precise statement, a prior-art gap, reproducible evidence and a path to external review.

The `01-` to `05-` folders are reading stages. File names stay descriptive; the stage number gives
the order. `checklist.md` tracks work across all stages.

## How to use this folder

1. Read the claim and current gaps on this page.
2. Establish the gap in [Positioning](01-positioning/prior-art.md).
3. Build the experiments in [Evaluation](02-evaluation/benchmark.md).
4. Run one study outside the test suite in [Validation](03-validation/plan.md).
5. Write and release from [Publication](04-publication/publication-plan.md).
6. Check the legal framing in [Governance](05-governance/eu-liability.md).
7. Track the work in [Checklist](checklist.md).

| Stage | Page | Contents |
|---|---|---|
| 01 | [Prior art](01-positioning/prior-art.md) | matrix, comparator discovery, fair comparison protocol |
| 01 | [Comparators](01-positioning/comparators.md) | documented and measured external comparison |
| 01 | [Formal model](01-positioning/formal-model.md) | definitions, score composition, invariants |
| 02 | [Benchmark](02-evaluation/benchmark.md) | hypotheses, metrics, benchmark protocol, threats |
| 02 | [Evidence map](02-evaluation/evidence-map.md) | claims, numbers, sources and missing evidence |
| 02 | [External benchmarks](02-evaluation/external-benchmarks.md) | world benchmarks, fit and run protocol |
| 02 | [Sev1-Bench](02-evaluation/sev1-bench.md) | external SRE incident run: DeepSeek baseline vs LAIX |
| 02 | [Continuity benchmark](02-evaluation/continuity-benchmark.md) | episode mechanism test: stateless vs stateful |
| 02 | [τ-bench](02-evaluation/tau-bench.md) | baseline 9/10 retail tasks; LAIX policy adapter pending |
| 03 | [Validation plan](03-validation/plan.md) | deployment, incident replay or vignette study |
| 03 | [Incident replay](03-validation/incident-replay.md) | collection plan, field mapping and fallback |
| 03 | [Vignette study](03-validation/vignette-study.md) | 20 vignettes and the blinded protocol |
| 03 | [Consent](03-validation/consent.md) | participant consent text |
| 03 | [Recruitment](03-validation/recruitment.md) | recruitment template |
| 04 | [Publication plan](04-publication/publication-plan.md) | reproducibility, paper outline, venues |
| 04 | [Paper draft](04-publication/paper-draft.md) | current draft with validation pending |
| 04 | [Artifact manifest](04-publication/artifact-manifest.md) | files to release |
| 04 | [References](04-publication/references.md) | sources to verify before citing |
| 04 | [Review log](04-publication/review-log.md) | reviewer comments and changes |
| 05 | [EU liability](05-governance/eu-liability.md) | PLD 2024/2853 mapping |
| — | [Checklist](checklist.md) | phased tasks from claim to external review |

## Snapshot

- Repository: `laix`
- Status at time of writing: Python and TypeScript tests, parity, conformance, bench and examples pass.
- Existing proof points: `LiveDecisionEngine`, the live decision benchmark, Python/TypeScript parity,
  conformance vectors, deterministic replay and the audit trail.
- Added: `01-positioning/comparators.md` (documented capability comparison, 7 systems), `05-governance/eu-liability.md`
  (PLD 2024/2853 mapping), `ablation_study.py` (all 7 planners on 7 demo cases, `LiveDecisionEngine` wins
  every case), `conflict_scenario.py` (triple-concern demo), `shadow_rollout.py` (rollout
  pattern).
- Added: `01-positioning/formal-model.md` with exact score formulas and weights, `01-positioning/prior-art.md` matrix
  (10 capabilities × 7 columns), `tests/core/test_invariants.py` (17 property tests, I1–I10),
  `benchmarks/live/v1/` (120 cases with dev/test/adversarial splits),
  `scripts/novelty/bench/run_live_bench.py` (metrics and bootstrap intervals),
  `scripts/novelty/analysis/analyze_results.py` (McNemar, paired bootstrap and effect sizes),
  `scripts/novelty/shared/glue_baseline.py` (hand-built integration baseline),
  `scripts/novelty/bench/validate_live_cases.py` (schema validation),
  `scripts/novelty/bench/run_ablations.py`, `scripts/novelty/bench/summarize_results.py`,
  `results/live-decision-benchmark/` (baseline, analysis and ablations), and a CI reproduction step.
- Measured result: `LiveDecisionEngine` 30/30 on the test split, but a hand-built glue baseline is 28/30.
  Against glue, +6.7 pp (95% CI 0.0–0.167, McNemar p = 0.48). The integration advantage over
  single-concern planners is large; the advantage over competent glue code is not yet significant.
- External operational result: the LangGraph adapter runs the same decision engine on 120 cases
  (6.9 ms mean, 110 glue lines, 0 interrupts). Temporal, PagerDuty and Camunda remain
  documented-only because they need servers or accounts.
- External benchmark: Sev1-Bench on all 20 scenarios. Baseline 0.800, LAIX guardrail 0.800,
  LAIX chooser 0.745 (one forbidden action). The benchmark scores single-turn diagnosis and
  remediation, not approvals, commitments, continuity or audit. See
  [Sev1-Bench](02-evaluation/sev1-bench.md).
- Continuity benchmark v0: 12 episodes, 60 decisions. Stateful `LiveDecisionEngine` 100% success,
  stateless `UtilityEngine` 0% with 36 continuity errors. Synthetic mechanism test, not external
  validation. See [continuity benchmark](02-evaluation/continuity-benchmark.md).
- Remaining gaps: no external runnable adapter for Temporal, PagerDuty or Camunda, no real-world
  deployment or incident replay, and no external review. The Sev1-Bench run is a component result,
  not a deployment.

## 1. What "novel" must mean here

Frame the contribution as a **systems and integration contribution**.

### The claim (after the prior-art matrix)

> LAIX is a training-free live decision runtime that places commitments, execution risk and human
> attention budget into one decision contract — the same object that carries the verb, the score,
> the reason code and the audit trail — while the host retains execution and delivery.
> No compared system (LangGraph, Temporal, PagerDuty, AutoGen, Camunda, FIPA/BDI, scikit-learn)
> carries all ten capabilities in one object. On the frozen test split `LiveDecisionEngine` is 30/30 and wins
> every conflict case; the best single-concern planner is 70%. A hand-built glue baseline reaches
> 93.3%, so the remaining integration advantage is +6.7 pp and is not significant on 30 cases.
> That is why real-world validation is still required.

### Why this claim is narrow enough to defend

The prior-art matrix (`01-positioning/prior-art.md`) shows what each category of system actually covers:

| Ingredient | Who already has it |
|---|---|
| Commitments in decisions | FIPA/BDI commitment protocols |
| Execution audit trail | Temporal, PagerDuty, Camunda |
| Calibration from outcomes | scikit-learn calibration |
| Host-owned execution | LangGraph, AutoGen, scikit-learn |
| Training-free defaults | all compared systems |

What is **not** found in any single compared system:

- commitments, execution risk and attention budget all in the same decision object;
- a formally defined revision semantics (I5) over a timeline;
- calibration piped back into the next decision without retraining.

The contribution is the contract and the composition. The individual ingredients are known. The
claim is that no existing system combines them into one live decision runtime with the same contract
and the same evidence.

`LiveDecisionEngine` is the proof object: one plan can keep a promise, avoid an irreversible action
and respect an attention budget at the same time.

### Scope

In scope:

- one decision contract for wait, observe, guide, ask, act, verify and escalate;
- commitments, execution risk and human attention as first-class decision terms;
- decision time, revisions and a timeline;
- calibration from measured outcomes;
- host-owned execution, receipts and recovery;
- deterministic, training-free operation;
- Python and TypeScript parity.

Out of scope:

- a new solver, planner or learning algorithm;
- model training or fine-tuning;
- orchestration, memory, UI, storage or delivery;
- a general-purpose agent framework;
- replacing domain policy or human judgment.

### What must not be claimed

- "First to use commitments, attention or execution risk." Each exists separately.
- "First to have an auditable decision trail." Temporal, PagerDuty and Camunda all have this.
- "First to have host-owned execution." LangGraph and AutoGen already do this.
- "State of the art on a public benchmark." There is no public benchmark yet.
- "Proven in production." There is no production study yet.
- "Novel because the code is clean." Engineering quality is not novelty.

## 2. Current assets and gaps

| Area | Current artifact | Status | Gap to close |
|---|---|---|---|
| Decision contract | `Decision`, `DecisionProblem`, `Plan`, `EnginePolicy` | exists | formal definition and invariants |
| Integrated planner | `LiveDecisionEngine` | exists | real validation still needed |
| Commitments | `Commitment`, `CommitmentLedger`, commitment planner | exists | larger conflict cases |
| Execution risk | execution planner, receipts, recovery | exists | measured irreversible-action reduction |
| Attention | attention planner, budget, signals | exists | measured budget adherence and interruption quality |
| Timing and revision | stream session, timeline | exists | formal revision invariants |
| Calibration | calibration and decision calibration | exists | held-out calibration report |
| Audit | receipts, traces, decision record | exists | replay and tamper evidence in evaluation |
| Parity | Python and TypeScript suites | exists | include in artifact release |
| Benchmark | 120 live cases + 7-case demo | **done** | harder real-incident cases |
| Ablation | 7 planner variants on the test split | **done** | — |
| Glue baseline | `scripts/novelty/shared/glue_baseline.py` | **done** | external adapters still missing |
| External adapter | LangGraph adapter, 120 decisions, 6.9 ms, 110 glue lines | **done** | Temporal/Camunda need servers |
| Significance | McNemar, paired bootstrap and effect sizes | **done** | +6.7 pp vs glue is not significant on 30 cases |
| Prior art | `01-positioning/comparators.md` (7 systems, documented capability comparison) | **done** | runnable adapter still missing |
| EU liability case | `05-governance/eu-liability.md` (PLD 2024/2853 field-by-field mapping) | **done** | — |
| Real validation | incident harness + 20 user-study vignettes ready; no data collected | missing | one deployment, replay or user study |
| Paper | draft in `04-publication/paper-draft.md`; validation pending | partial | final draft after real data |

## 3. Definition of done

Claim novelty in a paper, README or talk when these are true:

- [x] the claim is precise and narrow — §1 rewritten after the matrix; names which ingredients
  exist elsewhere; narrows what must not be claimed (audit trail, host-owned execution);
- [x] the prior-art matrix is complete and cited — `01-positioning/comparators.md` done (7 systems,
  search log, per-system paragraphs, defensible claims);
- [x] the formal model and invariants are documented — `01-positioning/formal-model.md` filled (types, score
  formulas with weights, state machines, invariants I1–I10); 17 property tests pass;
- [x] the benchmark has 100+ cases and held-out splits — 120 cases: 72 dev, 30 test,
  18 adversarial;
- [x] ablations show which term contributes what — test split: full 100%, no attention 96.7%,
  no feasibility gates 93.3%, no execution 83.3%, no commitment 70%, utility-only 30%;
- [x] confidence intervals and effect sizes are reported — 10,000-resample bootstrap and
  McNemar in `results/live-decision-benchmark/metrics/significance.json`;
- [x] the result against a hand-built glue baseline is reported honestly — +6.7 pp, p = 0.48;
- [ ] one real validation exists;
- [x] the artifact reproduces the main table with one command — `bash scripts/novelty/reproduce.sh`;
- [x] limitations are written down — threats and failure analysis in `02-evaluation/benchmark.md`;
- [ ] an external reader or reviewer has seen the draft.

Until then, use this wording:

> LAIX is an early systems contribution that combines commitments, execution risk and attention in
> one decision contract. The integration is implemented and tested; external validation is pending.

## 4. Starting on another computer

```powershell
git clone <repository-url>
cd laix

cd packages/python/laix
python -m pytest -q
ruff check .

cd ../typescript/laix
npm ci
npm run typecheck
npm test
npm run bench
npm run conformance

cd ../..
bash scripts/novelty/reproduce.sh
```

Then review:

1. `README.md` (this page);
2. `01-positioning/prior-art.md` and `01-positioning/comparators.md`;
3. `02-evaluation/benchmark.md` and `results/live-decision-benchmark/`;
4. `03-validation/plan.md` — the next external step.

First task now: choose the validation option and run it. The synthetic corpus is complete; move to
external validation with real incident data.

## 5. Open decisions

- Which domain for the real validation?
- Deployment, incident replay or user study?
- Which venue and paper length?
- Public benchmark or private evaluation set?
- Which claims are safe if the benchmark gives mixed results?
- Who is the independent reviewer or replication partner?

## 6. One-line summary

The work is not "invent a new planner". The work is "define, implement, compare and validate one
decision contract that makes commitments, execution risk, attention, timing, calibration and audit
parts of the same live decision".
