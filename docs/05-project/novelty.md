# Novelty and evidence plan

This is a working plan, not a claim that novelty is already established.

The goal is to make LAIX's contribution defensible to an external reviewer: a precise claim, a
documented prior-art gap, reproducible evidence, and at least one validation outside the test suite.

## Snapshot

- Repository: `laix`
- Status at time of writing: Python and TypeScript tests, parity, conformance, bench and examples pass.
- Existing proof points: `LiveDecisionEngine`, the live bench, Python/TypeScript parity,
  conformance vectors, deterministic replay and the audit trail.
- Main gap: no prior-art matrix, no ablation study, no confidence intervals, no real-world
  validation and no paper.

## 1. What "novel" must mean here

Do not claim a new algorithm. Claim a **systems and integration contribution**.

> LAIX is a training-free decision layer that unifies commitments, execution risk, human attention,
> decision timing, calibration and auditable revision in one decision contract, while the host keeps
> execution and delivery.

The contribution is the contract and the composition. The individual ingredients are known:
utility models, MDP/POMDP planning, commitments, interruption cost, sagas, calibration and audit
records. The claim is that no existing system combines them into one live decision layer with the
same contract and the same evidence.

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
- "State of the art on a public benchmark." There is no public benchmark yet.
- "Proven in production." There is no production study yet.
- "Novel because the code is clean." Engineering quality is not novelty.

## 2. Current assets and gaps

| Area | Current artifact | Status | Gap to close |
|---|---|---|---|
| Decision contract | `Decision`, `DecisionProblem`, `Plan`, `EnginePolicy` | exists | formal definition and invariants |
| Integrated planner | `LiveDecisionEngine` | exists | ablation and sensitivity study |
| Commitments | `Commitment`, `CommitmentLedger`, commitment planner | exists | larger conflict cases |
| Execution risk | execution planner, receipts, recovery | exists | measured irreversible-action reduction |
| Attention | attention planner, budget, signals | exists | measured budget adherence and interruption quality |
| Timing and revision | stream session, timeline | exists | formal revision invariants |
| Calibration | calibration and decision calibration | exists | held-out calibration report |
| Audit | receipts, traces, decision record | exists | replay and tamper evidence in evaluation |
| Parity | Python and TypeScript suites | exists | include in artifact release |
| Benchmark | LAIX-Bench 25 cases; live bench 7 cases | small | 100+ live cases with splits |
| Prior art | none documented | missing | feature matrix and citations |
| Real validation | none | missing | one deployment, replay or user study |
| Paper | none | missing | technical report and submission |

## 3. Prior-art analysis

### Deliverable

Create `docs/05-project/prior-art.md` with:

1. a feature matrix;
2. a short paragraph per compared system;
3. citations to primary sources and documentation;
4. a "closest prior work" statement;
5. a list of claims that remain defensible after the comparison.

### Matrix template

Use these columns. Mark each cell yes, partial, no, or unknown, and add evidence.

| Capability | Agent frameworks | Workflow engines | Alert/interruption systems | Commitment protocols | Execution/saga tools | Calibration tools | LAIX |
|---|---|---|---|---|---|---|---|
| One decision contract | | | | | | | yes |
| Commitments in the decision | | | | | | | yes |
| Execution risk in the decision | | | | | | | yes |
| Human attention budget | | | | | | | yes |
| Timing and revision semantics | | | | | | | yes |
| Calibration from outcomes | | | | | | | yes |
| Auditable decision trail | | | | | | | yes |
| Host-owned execution | | | | | | | yes |
| Training-free default | | | | | | | yes |
| Python/TypeScript parity | | | | | | | yes |

### Candidate categories to compare

Verify every entry against current documentation and primary sources before writing the final text.

- Agent orchestration: LangGraph, AutoGen, CrewAI, Semantic Kernel.
- Workflow and durable execution: Temporal, Airflow, Prefect, Netflix Conductor.
- Alerting and interruption management: PagerDuty, Opsgenie and similar on-call systems.
- Commitment protocols and multi-agent systems: FIPA ACL, commitment-based protocols, social
  commitments, normative multi-agent systems.
- Planning: MDP/POMDP solvers, POMDP libraries, HTN planning, options.
- Execution safety: sagas, compensation, idempotency, outbox and undo patterns.
- Calibration: reliability diagrams, Brier score, expected calibration error, decision calibration.
- Human-in-the-loop: mixed-initiative interaction, interruption cost, notification fatigue.

### Closest prior work statement

Write one paragraph that names the closest system in each category and explains the gap:

> The closest work in category X provides A and B, but not C. LAIX combines A, B and C in one
> contract and measures the combination on the same cases.

### Acceptance criteria

- At least 12 systems or research lines are compared.
- Every "yes" or "partial" has a citation or documentation link.
- The matrix does not use straw men.
- The claim is rewritten after the matrix so it is narrower if needed.

## 3.1 Comparison targets and fair comparison protocol

Novelty is not shown by LAIX's numbers alone. It is shown by **LAIX versus a fair alternative on the
same task**.

Use three comparison levels.

### Level 1: internal comparison (proves the integration)

This is the strongest and easiest comparison because the cases, inputs and outputs are identical.

| Comparator | What it tests |
|---|---|
| First option | naive baseline |
| Highest benefit | ignores safety, promises and attention |
| Utility only | no commitment, execution or attention terms |
| Commitment only | one concern |
| Execution only | one concern |
| Attention only | one concern |
| LAIX without commitments | ablation |
| LAIX without execution risk | ablation |
| LAIX without attention | ablation |
| LAIX with equal weights | weight sensitivity |
| LAIX without feasibility gates | gate sensitivity |

Report every comparator on the same cases, splits and metrics.

### Level 2: external system comparison (proves the gap)

Compare against the closest system in each category. Run a **task-aligned adapter** where possible;
otherwise compare documented capabilities and say so explicitly.

| Category | Candidate comparators | What to compare | How |
|---|---|---|---|
| Agent orchestration | LangGraph, AutoGen, CrewAI, Semantic Kernel | one decision contract, commitments, approval, interrupts, replay | adapter or documented comparison |
| Durable workflows | Temporal, Airflow, Prefect, Netflix Conductor | approvals, retries, compensation, audit, recovery | adapter or documented comparison |
| Incident and alerting | PagerDuty, Opsgenie, Grafana OnCall | interruption policy, escalation, on-call budget | rules adapter or documented comparison |
| Commitment protocols | FIPA ACL, commitment-based multi-agent systems, BDI agents | promise state, violation, dependency handling | conceptual comparison and small prototype |
| Planning | MDP/POMDP solvers, HTN and PDDL planners | decision quality under uncertainty | same case harness where feasible |
| Execution safety | saga pattern, Camunda, Temporal | undo, compensation, receipts, idempotency | adapter or documented comparison |
| Calibration | scikit-learn calibration, conformal prediction | ECE, Brier score, decision accuracy | same outcome data |
| Human-in-the-loop | mixed-initiative and interruption research | attention cost, acceptance, timing | user study or simulation |

Do not compare LAIX to an agent framework on general agent tasks. Compare on the **live decision
task**: one request, one decision, with promises, execution risk, attention and audit.

### Level 3: operational comparison (proves practicality)

Numbers reviewers ask for that are not accuracy:

| Metric | Why it matters |
|---|---|
| Glue code lines | how much host code the integration needs |
| Configuration size | how many rules or settings the host must write |
| External dependencies | services, databases or SDKs required |
| Cold-start and p95 latency | whether it fits the live window |
| Deployment complexity | number of moving parts |
| Failure modes | what happens when a dependency is down |
| Audit completeness | whether a decision can be replayed |

### Fairness rules

1. Use the same cases, inputs, expected actions and splits for every comparator.
2. Give each comparator its strongest reasonable configuration.
3. Tune on the dev split only; freeze the test split before the final run.
4. Record the exact version, commit, configuration and seed.
5. Do not use a straw-man baseline.
6. If a system cannot be run, say "documented capability comparison" and do not report invented
   performance numbers.
7. Separate "out-of-the-box" from "task-aligned adapter" results.
8. Report negative and mixed results.
9. Report integration effort and operational cost, not only accuracy.
10. Keep the comparison protocol in the artifact.

### Comparison reporting table

| Comparator | Version | Capability score | Accuracy | Promise keeping | Irreversible rate | Budget violations | p95 latency | Glue LoC | External deps |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| First option | — | | | | | | | | |
| Highest benefit | — | | | | | | | | |
| Utility only | — | | | | | | | | |
| Commitment only | — | | | | | | | | |
| Execution only | — | | | | | | | | |
| Attention only | — | | | | | | | | |
| LAIX integrated | | | | | | | | | |
| External system A | | | | | | | | | |
| External system B | | | | | | | | | |

The **capability score** is the number of capabilities covered out of the matrix above. The
**integration delta** is LAIX minus the best non-LAIX comparator on the same metric. Report both.

### What "compare to whom" means in the paper

- **Primary comparison:** internal ablations and single-concern planners. This proves that the
  integration does work.
- **Secondary comparison:** closest external system in each category. This proves the gap is real.
- **Tertiary comparison:** closest academic line in related work. This positions the contribution.
- **Not a comparison:** LAIX versus a full agent framework on general agent benchmarks. That is a
  different task and would be an unfair comparison.

### Acceptance criteria

- At least one external comparator per relevant category.
- At least one task-aligned adapter, not only a documentation table.
- All comparators share the same cases and metrics.
- The paper reports both capability and performance comparisons.
- The limitations section names every comparison that could not be run.

## 4. Formal contribution

### Deliverable

Create `docs/05-project/formal-model.md` with the decision problem, scoring composition, feasibility
rules and state transitions. Add property tests that fail if an invariant is broken.

### Definitions to write down

- `DecisionProblem`: subject, time, situation, options, signals, context, attributes.
- `ActionOption`: verb, benefit, cost, risk, latency, interruption, reversibility,
  approval, execution facts, commitment effects.
- `Commitment`: id, subject, due time, status, dependencies, priority.
- `AttentionBudget`: total, spent, remaining.
- `ExecutionReceipt`: status, actor, approval, idempotency key, detail, previous state.
- `Plan`: chosen verb/action, confidence, score, alternatives, attributes.
- `Decision`: public contract derived from a plan.
- `Revision`: revision number, predecessor, event time, stream id, status.
- `Timeline`: append-only set with revision rules.

### Score composition

Document the actual formula used by `LiveDecisionEngine`:

```text
total = utility + commitment + execution + attention
```

For each term, define:

- inputs;
- weights and defaults;
- feasibility gates;
- tie-breaking;
- why a term can veto an option;
- what happens when a term is unknown.

### Invariants

Write tests for at least these:

1. The same problem and configuration produce the same plan.
2. A hard constraint cannot be outscored by a high utility.
3. Attention spent never exceeds the budget and never becomes negative.
4. A rejected approval cannot be selected.
5. A higher revision always has a predecessor and never moves event time backwards.
6. A receipt follows a valid state machine:
   `pending -> approved -> executed -> undone`, with `unknown`, `failed`, `refused`,
   `cancelled` handled explicitly.
7. A decision trace is append-only.
8. Calibration never produces a confidence outside `[0, 1]`.
9. Simulation and live planning use the same contract conversion.
10. Python and TypeScript produce the same decision for shared cases.

### Acceptance criteria

- Every invariant has a test that would fail if the code regressed.
- The document explains the contribution without relying on code comments.
- The formulas match the implementation.

## 5. Hypotheses and metrics

Define hypotheses before running the expanded benchmark.

| ID | Hypothesis | Metric | Baseline | Success criterion |
|---|---|---|---|---|
| H1 | Integrated planning keeps more promises | promise-keeping rate | utility-only | higher with a non-trivial effect size |
| H2 | Integrated planning chooses fewer irreversible actions | irreversible-action rate | highest-benefit | lower without collapsing to wait |
| H3 | Integrated planning respects attention budgets | budget violations, attention spend | attention-only | no increase in violations, lower spend |
| H4 | Calibration improves decision accuracy | accuracy, ECE, Brier | uncalibrated | lower ECE and equal or better accuracy |
| H5 | Integration does not damage plain decisions | accuracy on plain cases | utility-only | no significant regression |
| H6 | The live path remains fast and deterministic | p95 latency, replay equality | single-concern planners | inside the live window, replay equal |
| H7 | Integration wins when concerns conflict | accuracy on conflict cases | every single-concern planner | integrated wins or ties on most cases |
| H8 | Audit and replay are usable | replay equality, trace completeness | none | every decision replayable and traced |

Do not add a hypothesis after seeing the results. Record it, then run the test.

## 5.1 How to turn each claim into a number

Reviewers want a table where every sentence has a metric, a baseline, a confidence interval and an
effect size. Use this mapping.

| Claim | Number | Definition | Baseline | Expected direction |
|---|---|---|---|---|
| Integration is real | conflict win rate | share of conflict cases where LAIX matches or beats the best single-concern planner | best single-concern planner | higher |
| Integration adds value | integration delta | `accuracy(LAIX) - max(accuracy(single-concern))` on conflict cases | best single-concern | positive |
| Integration is not a wrapper | ablation delta | metric loss when one term is removed | full `LiveDecisionEngine` | removal hurts |
| Plain decisions are not damaged | plain-case regret | mean utility gap to the best feasible option on plain cases | utility-only | near zero |
| Promises are kept | promise-keeping rate | fulfilled commitments / relevant commitments | utility-only | higher |
| Irreversible actions are avoided | irreversible-action rate | irreversible choices / actionable cases | highest-benefit | lower |
| Attention is respected | budget-violation rate | cases where attention cost exceeds remaining budget / human-facing cases | attention-only | no worse |
| Attention is not wasted | mean attention spend | mean attention cost per case | attention-only | lower or equal |
| Safety is preserved | safety-violation rate | hard-constraint violations / cases | highest-benefit | lower |
| Calibration works | ECE and Brier score | calibration error on held-out outcomes | uncalibrated | lower |
| The live path is usable | p95 latency | 95th percentile decision latency in ms | single-concern planners | inside the live window |
| Results are reproducible | replay equality | share of cases with identical decisions on replay | itself | 100% |
| The artifact is auditable | trace completeness | decisions with a complete trace / decisions | none | 100% |

### Per-case record

Log one row per case and planner. Every metric above should be derivable from this record:

```json
{
  "case_id": "string",
  "category": "promise | execution | attention | timing | conflict | plain",
  "split": "dev | test | adversarial",
  "planner": "string",
  "chosen_action": "string | null",
  "expected_actions": ["string"],
  "acceptable_actions": ["string"],
  "correct": true,
  "feasible": true,
  "safety_violation": false,
  "irreversible": false,
  "promise_fulfilled": true,
  "attention_cost": 0.0,
  "attention_remaining": 0.0,
  "utility_chosen": 0.0,
  "utility_best_feasible": 0.0,
  "latency_ms": 0.0,
  "confidence": 0.0,
  "seed": 0
}
```

### Formulas

Use these definitions in the analysis script:

```text
accuracy            = correct / N
promise-keeping     = fulfilled commitments / relevant commitments
irreversible rate   = irreversible choices / actionable cases
budget violations   = (attention_cost > attention_remaining) / human-facing cases
safety violations   = hard-constraint violations / N
plain-case regret   = mean((utility_best - utility_chosen) / max(|utility_best|, 1e-9))
abstention rate     = wait decisions / N
conflict win rate   = cases(LAIX >= best single-concern) / conflict cases
integration delta   = accuracy(LAIX) - max(accuracy(single-concern))
ablation delta      = metric(full) - metric(term removed)
ECE                 = sum_b (n_b / N) * |accuracy_b - confidence_b|
Brier score         = mean((confidence - correct)^2)
p95 latency         = 95th percentile of latency_ms
replay equality     = identical decisions on replay / N
```

For utility regret, report both the mean and the share of cases with a gap above a stated threshold
(for example 0.05 or 0.10). A mean alone can hide a few bad cases.

### Reporting template

Main table:

| Planner | Accuracy | 95% CI | Promise keeping | Irreversible rate | Budget violations | p95 latency |
|---|---:|---:|---:|---:|---:|---:|
| First option | | | | | | |
| Highest benefit | | | | | | |
| Utility only | | | | | | |
| Commitment only | | | | | | |
| Execution only | | | | | | |
| Attention only | | | | | | |
| LAIX integrated | | | | | | |

Conflict cases only:

| Planner | Conflict accuracy | Integration delta | Plain-case regret | Abstention rate |
|---|---:|---:|---:|---:|
| Best single-concern | | | | |
| LAIX integrated | | | | |

Ablation table:

| Variant | Accuracy | Promise keeping | Irreversible rate | Budget violations |
|---|---:|---:|---:|---:|
| Full LAIX | | | | |
| Without commitment term | | | | |
| Without execution term | | | | |
| Without attention term | | | | |
| Equal weights | | | | |
| No feasibility gates | | | | |

Calibration table:

| Planner | Accuracy | ECE | Brier | Decision accuracy at 0.8 confidence |
|---|---:|---:|---:|---:|
| Uncalibrated | | | | |
| Calibrated | | | | |

Prior-art coverage table:

| System | Capabilities covered | Unique to LAIX |
|---|---:|---:|
| Compared system A | | |
| Compared system B | | |
| LAIX | 10 / 10 | — |

The coverage table is supporting evidence, not a substitute for performance numbers. A reviewer
will trust “LAIX keeps 18% more promises with a 2% utility cost” more than “LAIX covers 10 features”.

### Statistical tests

- **Paired bootstrap** over cases, 10,000 resamples, for every headline metric.
- **McNemar's test** for paired binary correctness.
- **Wilcoxon signed-rank** for latency and utility regret.
- **Holm–Bonferroni** correction when testing several hypotheses.
- Report the number of cases, the mean, the 95% confidence interval, the effect size and the p-value.
- For proportions, report Cohen's h or the risk difference.
- For utility and latency, report the median and the paired difference.

A result without an interval is a point estimate, not evidence. A result without a baseline is not a
result.

### Power and sample size

Do a simulation-based power analysis before freezing the test set. The required size depends on how
often the planners disagree. As a practical rule:

- 40+ discordant cases are a minimum for a paired accuracy comparison;
- 100+ cases per split are safer;
- more cases are needed for rare events such as irreversible actions and safety violations.

Record the assumed effect size and the resulting power in the paper.

### What reviewers will look for

1. Absolute numbers, not only percentages.
2. Confidence intervals and effect sizes.
3. A strong baseline, not a straw man.
4. Per-category results, not one aggregate.
5. Negative and mixed results.
6. A failure analysis with examples.
7. Exact commands, seeds, versions and hardware.
8. A public artifact or a clear reason why it is private.
9. A clear separation between benchmark evidence and real-world evidence.
10. Claims that do not exceed the numbers.

## 6. Benchmark protocol

### Deliverable

Create:

- `benchmarks/live/cases.v1.json`
- `benchmarks/live/README.md`
- `scripts/run_live_bench_v2.py`
- `scripts/run_ablations.py`
- `scripts/summarize_results.py`
- `results/live_bench_v2/` (generated, versioned summary committed)

### Case schema

Each case should carry:

```json
{
  "id": "string",
  "category": "promise | execution | attention | timing | conflict | plain",
  "problem": {},
  "expected_actions": ["string"],
  "acceptable_actions": ["string"],
  "tags": ["string"],
  "notes": "string",
  "difficulty": "easy | medium | hard",
  "split": "dev | test | adversarial"
}
```

### Coverage target

Start with 120 cases:

| Category | Cases | Purpose |
|---|---:|---|
| Promise keeping | 20 | conflicting promises, due dates, dependencies |
| Execution risk | 20 | irreversible, unknown, approval, recovery |
| Attention | 20 | interruption, approval, escalation, exhausted budget |
| Timing | 15 | deadline, late event, revision, cooldown |
| Conflict | 25 | two or more concerns disagree |
| Plain utility | 20 | no special concern; catch regressions |

Splits:

- dev: 60 cases, used while developing;
- test: 40 cases, used once for the main table;
- adversarial: 20 held-out cases, written last and not inspected during tuning.

### Baselines

- first option;
- highest benefit;
- utility-only;
- commitment-only;
- execution-only;
- attention-only;
- integrated live planner.

### Ablations

Run `LiveDecisionEngine` with each term removed:

- no commitment term;
- no execution term;
- no attention term;
- utility only;
- all terms but with equal weights;
- all terms but with no feasibility gates.

This shows which term carries which result and whether the integration is doing real work.

### Metrics

Per planner and per category:

- correctness against expected action;
- acceptable-action rate;
- promise-keeping rate;
- irreversible-action rate;
- attention spend and budget violations;
- safety violations;
- mean and p95 latency;
- mean score;
- abstention rate (`wait`);
- calibration error where confidence is reported;
- failure-case list.

### Statistics

- Run five seeds where randomness exists.
- Report bootstrap 95% confidence intervals.
- Use paired comparisons on the same cases.
- Report effect sizes, not only p-values.
- Keep a fixed test split.
- Record the exact command, commit and environment in the results file.

### Acceptance criteria

- The main table can be regenerated by one command.
- Every headline claim maps to a table row.
- Negative and mixed results are reported.
- The adversarial split is not used for tuning.

## 7. Real-world validation

Synthetic cases are not enough. Choose one:

### Option A: deployment or pilot

- one host application;
- two to four weeks;
- log decisions, approvals, executions and outcomes;
- measures: promise keeping, irreversible actions, attention spend, missed deadlines,
  undo rate, acceptance rate.

### Option B: incident or support replay

- take historical events;
- replay through LAIX and the baseline;
- compare decisions against what a human did;
- report disagreements and their costs.

### Option C: user study

- ask operators to judge decisions from LAIX and a baseline;
- blind the source;
- measure acceptance, perceived timeliness, trust and workload;
- include a sample-size justification.

For all options, document consent, privacy, data minimisation and retention. Do not include
personal data in the public artifact.

### Acceptance criteria

- At least one validation outside the repository test suite.
- A clear method section and a limitations section.
- Raw data is either public or its absence is justified.

## 8. Reproducibility and artifact

Create or update:

- `CITATION.cff`
- `LICENSE` reference in the paper
- `scripts/reproduce_novelty.py`
- a pinned environment file
- a CI job that runs the novelty benchmark
- a versioned release and DOI (for example through Zenodo)
- `results/` with the exact output of the reported run

Acceptance criteria:

- A fresh clone can reproduce the main table.
- The paper states the commit hash and package versions.
- The artifact includes Python and TypeScript conformance cases.
- No secret or personal data is required.

## 9. Paper and dissemination

### Working title

> One decision contract for live AI: commitments, execution risk and attention in a single layer

### Abstract skeleton

1. live AI systems need timely, safe and auditable decisions;
2. existing tools cover orchestration, workflows, alerting or planning separately;
3. LAIX contributes one contract and one integrated planner;
4. evaluation on N cases and one real validation;
5. limitations and open problems.

### Section outline

1. Introduction and problem.
2. Related work and prior-art gap.
3. Decision contract and formal model.
4. Integrated live planner.
5. Execution, audit and revision semantics.
6. Calibration and outcome learning.
7. Implementation and parity.
8. Evaluation: benchmark, ablations and validation.
9. Threats to validity.
10. Conclusion and future work.

### Claim-evidence map

Create a table in the paper and in `docs/05-project/novelty-evidence.md`:

| Claim | Evidence | Artifact |
|---|---|---|
| Integration improves promise keeping | H1 table | benchmark |
| Execution risk reduces irreversible actions | H2 table | benchmark |
| Attention budget is respected | H3 table | benchmark |
| Calibration reduces error | H4 table | calibration report |
| Live path is deterministic and fast | H6 table | replay and latency results |
| The layer works outside tests | validation section | deployment/replay/study |

### Venues to consider

- AAMAS: agents, commitments, multi-agent decisions.
- IUI or CHI: mixed-initiative, interruption and human attention.
- HHAI: human-centered AI systems.
- NeurIPS Datasets and Benchmarks or a similar track: benchmark and artifact.
- A systems or software-engineering venue if the contract and implementation are the focus.

Choose the venue after the evidence exists, not before.

## 10. Phased checklist

### Phase 0: claim and prior art

- [ ] Write the one-paragraph claim.
- [ ] Write scope and non-goals.
- [ ] Build the prior-art matrix.
- [ ] Write the closest-prior-work paragraph.
- [ ] Rewrite the claim after the matrix.
- Deliverable: `docs/05-project/prior-art.md`.
- Done when an external reader can see exactly what is new and what is not.

### Phase 1: formal model and invariants

- [ ] Define the problem, score and feasibility.
- [ ] Define revision and receipt state machines.
- [ ] Write invariants I1-I10.
- [ ] Add property tests.
- Deliverable: `docs/05-project/formal-model.md` and tests.
- Done when every invariant has a failing test when broken.

### Phase 2: benchmark v2

- [ ] Create the case schema.
- [ ] Write 120 cases across the six categories.
- [ ] Freeze dev and test splits.
- [ ] Implement baselines and ablations.
- [ ] Add bootstrap confidence intervals.
- [ ] Add one-command reproduction.
- Deliverable: `benchmarks/live/` and `scripts/run_live_bench_v2.py`.
- Done when the main table is reproducible and includes negative results.

### Phase 3: real validation

- [ ] Choose deployment, replay or user study.
- [ ] Define metrics and sample size.
- [ ] Collect and anonymise data.
- [ ] Run the analysis.
- [ ] Write method and limitations.
- Deliverable: validation section and data statement.
- Done when there is evidence outside the repository tests.

### Phase 4: paper

- [ ] Write the abstract and claim-evidence map.
- [ ] Write related work from the matrix.
- [ ] Write the formal model.
- [ ] Write the evaluation.
- [ ] Write threats to validity.
- [ ] Internal review and reproducibility check.
- Deliverable: technical report or submission draft.

### Phase 5: artifact and release

- [ ] Add `CITATION.cff`.
- [ ] Add the reproduction script and CI job.
- [ ] Tag a release.
- [ ] Archive with a DOI.
- [ ] Publish the benchmark and conformance cases.
- Done when a fresh clone reproduces the reported tables.

### Phase 6: external review

- [ ] Submit to a venue.
- [ ] Respond to reviewers with new evidence, not new claims.
- [ ] Invite independent replication.
- [ ] Update the docs with the final claim.

## 11. Threats to validity

Document these explicitly:

- synthetic cases may not represent real traffic;
- the benchmark may encode the authors' assumptions;
- the integrated planner may win because the baselines are weak;
- a single domain limits generality;
- deterministic cases hide variance;
- the attention model is a simplification of human workload;
- calibration needs enough outcomes and may be noisy;
- the framework is model-free and does not cover learned policies;
- author-run evaluation creates bias;
- parity tests prove consistency, not correctness.

Mitigations:

- independent case authors;
- strong and tuned baselines;
- held-out and adversarial splits;
- multiple domains;
- confidence intervals and effect sizes;
- external review and replication;
- publish negative results.

## 12. Definition of done

Do not claim novelty in a paper, README or talk until all of these are true:

- [ ] the claim is precise and narrow;
- [ ] the prior-art matrix is complete and cited;
- [ ] the formal model and invariants are documented;
- [ ] the benchmark has 100+ cases and held-out splits;
- [ ] ablations show which term contributes what;
- [ ] confidence intervals and effect sizes are reported;
- [ ] one real validation exists;
- [ ] the artifact reproduces the main table;
- [ ] limitations are written down;
- [ ] an external reader or reviewer has seen the draft.

Until then, use this wording:

> LAIX is an early systems contribution that combines commitments, execution risk and attention in
> one decision contract. The integration is implemented and tested; external validation is pending.

## 13. Starting on another computer

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
```

Then open:

1. `docs/05-project/novelty.md` (this file);
2. `docs/05-project/prior-art.md` (create it first);
3. `docs/05-project/formal-model.md` (create it second);
4. `benchmarks/live/README.md` (create it third).

First task: write the claim and the prior-art matrix. Do not start with more code.

## 14. Open decisions

- Which domain for the real validation?
- Deployment, incident replay or user study?
- Which venue and paper length?
- Public benchmark or private evaluation set?
- Which claims are safe if the benchmark gives mixed results?
- Who is the independent reviewer or replication partner?

## 15. References to verify

This is a reading list, not a citation list. Verify every source before using it.

- Sagas and compensation: Garcia-Molina and Salem, 1987.
- MDP and POMDP planning: Sutton and Barto; Kaelbling, Littman and Cassandra.
- Mixed-initiative and interruption: Horvitz, 1999, and later HCI work on notification cost.
- Commitments and normative multi-agent systems: Singh, Chopra and related work.
- Calibration: Brier, 1950; Murphy, 1973; modern expected-calibration-error papers.
- Durable execution and workflow systems: Temporal, Airflow and Prefect documentation.
- Agent orchestration: LangGraph, AutoGen, CrewAI and Semantic Kernel documentation.
- Alerting and on-call: PagerDuty and Opsgenie documentation and incident-response literature.

## 16. One-line summary

The work is not "invent a new planner". The work is "define, implement, compare and validate one
decision contract that makes commitments, execution risk, attention, timing, calibration and audit
parts of the same live decision".
