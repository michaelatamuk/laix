# Evaluation and measurement

Turn every claim into a metric, a baseline and an interval. This page covers hypotheses, measurement
formulas, the benchmark protocol and threats to validity.

## 1. Hypotheses and metrics

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

## 2. How to turn each claim into a number

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

## 3. Benchmark protocol

### Deliverable

Create:

- `benchmarks/live/v1/dev.json`
- `benchmarks/live/v1/test.json`
- `benchmarks/live/v1/adversarial.json`
- `benchmarks/live/README.md`
- `scripts/novelty/bench/generate_live_cases.py`
- `scripts/novelty/bench/run_live_bench_v2.py`
- `scripts/novelty/bench/run_ablations.py`
- `scripts/novelty/bench/summarize_results.py`
- `results/live-bench/harness-v2/` (generated, versioned summary committed)

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

- dev: 72 cases, used while developing;
- test: 30 cases, frozen for the main table;
- adversarial: 18 held-out cases, written last and not used for tuning.

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

## 4. Threats to validity

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

## 5. Results and failure analysis

Generated from the frozen test split (30 cases) and the six ablations. The raw rows are in
`results/live-bench/harness-v2/raw.jsonl`; the summary is in `results/live-bench/harness-v2/reports/summary.json`; the
baseline is `results/live-bench/harness-v2/baseline.json`.

### Main table (test split, 30 cases)

| Planner | Accuracy | 95% CI | Promise keeping | Irreversible rate | Budget violations |
|---|---:|---:|---:|---:|---:|
| first | 70.00% | 0.53–0.87 | 58.33% | 13.33% | 77.78% |
| benefit | 23.33% | 0.10–0.40 | 0.00% | 23.33% | 70.00% |
| utility | 30.00% | 0.13–0.47 | 0.00% | 23.33% | 70.00% |
| commitment | 70.00% | 0.53–0.87 | 100.00% | 13.33% | 57.14% |
| execution | 50.00% | 0.33–0.67 | 8.33% | 6.67% | 62.50% |
| attention | 53.33% | 0.37–0.70 | 25.00% | 16.67% | 0.00% |
| **glue** | **93.33%** | **0.83–1.00** | **100.00%** | **0.00%** | **0.00%** |
| **live** | **100.00%** | **1.00–1.00** | **100.00%** | **0.00%** | **0.00%** |

### Conflict cases (6 cases)

| Planner | Conflict accuracy | 95% CI |
|---|---:|---:|
| first | 0.00% | 0.00–0.00 |
| benefit | 0.00% | 0.00–0.00 |
| utility | 0.00% | 0.00–0.00 |
| commitment | 83.33% | 0.50–1.00 |
| execution | 33.33% | 0.00–0.67 |
| attention | 66.67% | 0.33–1.00 |
| **glue** | **100.00%** | **1.00–1.00** |
| **live** | **100.00%** | **1.00–1.00** |

### Ablations (test split, 30 cases)

| Variant | Accuracy | Promise keeping | Irreversible rate | Budget violations |
|---|---:|---:|---:|---:|
| full | 100.00% | 100.00% | 0.00% | 0.00% |
| equal weights | 100.00% | 100.00% | 0.00% | 0.00% |
| no attention | 96.67% | 100.00% | 0.00% | 0.00% |
| no feasibility gates | 93.33% | 100.00% | 0.00% | 0.00% |
| no execution | 83.33% | 100.00% | 10.00% | 0.00% |
| no commitment | 70.00% | 25.00% | 6.67% | 0.00% |
| utility only | 30.00% | 0.00% | 23.33% | 70.00% |

The ablation is the important number: removing commitments costs 30 accuracy points, removing
execution risk costs 16.7, and removing attention costs 3.3. The integration is doing real work.

### Paired significance (test split, 30 cases)

`glue` is a hand-built integration baseline: hard gates, then commitments, then reversibility,
then attention, then utility. It is a stronger comparator than any single-concern planner.

| Comparator | Accuracy delta | 95% CI | Discordant (live / other) | McNemar chi² | p | Cohen's h |
|---|---:|---:|---:|---:|---:|---:|
| benefit | +76.7 pp | 0.600–0.900 | 23 / 0 | 21.043 | <0.001 | 2.133 |
| utility | +70.0 pp | 0.533–0.867 | 21 / 0 | 19.048 | <0.001 | 1.982 |
| execution | +50.0 pp | 0.333–0.667 | 15 / 0 | 13.067 | <0.001 | 1.571 |
| attention | +46.7 pp | 0.300–0.633 | 14 / 0 | 12.071 | <0.001 | 1.504 |
| commitment | +30.0 pp | 0.133–0.467 | 9 / 0 | 7.111 | 0.008 | 1.159 |
| first | +30.0 pp | 0.133–0.467 | 9 / 0 | 7.111 | 0.008 | 1.159 |
| **glue** | **+6.7 pp** | **0.000–0.167** | **2 / 0** | **0.500** | **0.480** | **0.522** |

The comparison against the hand-built glue baseline is the honest one: `live` is better, but the
confidence interval includes zero and the result is not significant on 30 cases. The integration
advantage over single-concern planners is large and significant; the advantage over competent glue
code needs a larger and harder corpus, and that is exactly what the real validation must test.

### Failure analysis

`live` made zero mistakes on the 30 test cases and zero on the 18 adversarial cases. That is a
warning, not a victory: the corpus is synthetic and currently too easy. The next evidence step must
add cases where the planner is expected to fail or abstain:

- ambiguous trade-offs where the domain expert disagrees with the score;
- noisy or missing outcomes;
- multi-step dependencies that cross decisions;
- long-tail incidents from real traffic;
- host-specific approval and recovery behaviour.

Record every new failure in this section with the case id, chosen action, expected action and the
term that dominated incorrectly. A benchmark with no failures cannot support a strong novelty
claim; the real-world validation in `validation.md` is still required.

### Reproduce

```bash
python scripts/novelty/bench/run_live_bench_v2.py --split test --seed 42
python scripts/novelty/bench/run_ablations.py --split test --seed 42
python scripts/novelty/bench/summarize_results.py
```

or, in CI, `bash scripts/novelty/reproduce.sh`.
