# Novelty checklist

Work through the phases in order. Move to the paper when the evidence exists.

---

## Phase 0: claim and prior art

- [x] Write the one-paragraph claim — `README.md` §1
- [x] Write scope and non-goals — `README.md` §1
- [x] Build the prior-art matrix — `01-positioning/comparators.md` (documented capability comparison,
  LangGraph, Temporal, PagerDuty, AutoGen, Camunda, FIPA/BDI, scikit-learn calibration)
- [x] Write the closest-prior-work paragraph — `01-positioning/comparators.md` §"Closest prior work statement"
- [x] Write the EU liability case — `eu-liability.md` (maps every decision field to PLD 2024/2853)
- [x] Fill the matrix table in `01-positioning/prior-art.md` from `01-positioning/comparators.md` — done; 10 capabilities ×
  7 columns with 14 footnotes citing primary sources
- [x] Rewrite the claim after the matrix — §1 rewritten; names which ingredients are found
  elsewhere and what no single system combines; "must not be claimed" extended with audit trail
  and host-owned execution (which Temporal/AutoGen already have)

**Deliverable:** `01-positioning/prior-art.md` complete with citations and the claim narrowed to what the matrix
actually shows. **DONE.**

---

## Phase 1: formal model and invariants

- [x] Define the problem, score and feasibility in `01-positioning/formal-model.md` — exact formulas and
  weights for `UtilityPlanner`, `CommitmentPlanner`, `ExecutionRiskPlanner` and
  `HumanAttentionPlanner`
- [x] Define revision and receipt state machines — documented in `01-positioning/formal-model.md` §3
- [x] Write invariants I1–I10 as statements in `01-positioning/formal-model.md` — §4 invariant table complete
- [x] Add property tests: `tests/core/test_invariants.py` — 17 tests, all pass

**Deliverable:** `01-positioning/formal-model.md` filled + tests. Every invariant has a failing test when broken.
**DONE.**

---

## Phase 2: benchmark v2

**Goal:** a 120-case benchmark with held-out splits, reproducible with one command, with bootstrap
confidence intervals.

### Done

- [x] Implement baselines and ablations — `examples/python/core/evaluation/bench/ablation_study.py`
  runs all 7 planners on all 7 demo cases; LiveCompositePlanner 7/7, single-concern planners partial
- [x] Write the conflict scenario — `examples/python/core/decision/history/conflict_scenario.py`
  shows all three concerns firing; `UtilityPlanner` and `HumanAttentionPlanner` fail; full score breakdown
- [x] Create the case schema — `benchmarks/live/v1/schema.json` (JSON Schema Draft
  2020-12); `benchmarks/live/README.md` with field reference, split targets and Python loader
  snippet

### Done

- [x] **Write 120 cases** in `benchmarks/live/v1/`:
  - `dev.json` — 72 cases;
  - `test.json` — 30 cases, frozen for the main table;
  - `adversarial.json` — 18 held-out cases.
  - Category distribution across all files: promise 20, execution 20, attention 20,
    timing 15, conflict 25, plain 20.
  - Generated deterministically by `scripts/novelty/bench/generate_live_cases.py`; every file validates
    against `schema.json`.

- [x] **Use a dependency-free bootstrap** — `run_live_bench.py` uses a pure-Python
  bootstrap (10,000 resamples, `random.Random(seed)`), so no `numpy` extra is required.

- [x] **Write `scripts/novelty/bench/run_live_bench.py`**:
  - loads the split files;
  - runs all 7 planners;
  - computes accuracy, promise keeping, irreversible rate, budget violations, safety, latency,
    regret and conflict accuracy with 95% bootstrap intervals;
  - writes `results/live-decision-benchmark/raw/decisions.jsonl` and `results/live-decision-benchmark/metrics/summary.json`;
  - prints the main and conflict tables;
  - exits 1 if `LiveCompositePlanner` fails a conflict case.

- [x] **Write `scripts/novelty/bench/run_ablations.py`**:
  - full, no commitment, no execution, no attention, utility-only, equal weights and
    no-feasibility-gates variants;
  - `LiveCompositePlanner(enforce_feasibility=False)` supports the last variant;
  - writes `results/live-decision-benchmark/ablations/results.json`.

- [x] **Write `scripts/novelty/bench/summarize_results.py`**:
  - compares `metrics/summary.json` against `metrics/baseline.json`;
  - prints a diff table;
  - exits 1 if accuracy, promise keeping, irreversible rate or budget violations move by more
    than 0.5 percentage points.

- [x] **Commit the baseline** — `results/live-decision-benchmark/metrics/baseline.json` and `metrics/summary.json` are
  the frozen test-split output (`split: test`, `seed: 42`, 30 cases).

- [x] **TypeScript live-bench parity** — `packages/typescript/laix/scripts/live-bench.mjs`
  runs the same test split and compares 210 action IDs with Python; all 210 agree.

- [x] **Run the available external adapter** — `benchmarks/compare/adapters/langgraph/adapter.py` runs
  the same composite planner on 120 cases (6.9 ms mean, 110 glue lines). Temporal, PagerDuty and Camunda
  remain documented-only.

- [x] **Write the failure analysis** — `LiveCompositePlanner` made zero mistakes on the 30 test cases and zero on
  the 18 adversarial cases. The zero-failure result is documented in `02-evaluation/benchmark.md` §5 as a
  limitation; the corpus is too easy, and real-incident cases are required next.

- [x] **Freeze the test split** — dataset version `1.0.0`; do not change the test cases again
  without a new version and a new baseline.

**Deliverable:** `benchmarks/live/v1/` (120 cases), `scripts/novelty/bench/run_live_bench.py`,
`scripts/novelty/bench/run_ablations.py`, `scripts/novelty/bench/summarize_results.py`,
`results/live-decision-benchmark/`. Main table reproducible with:
`python scripts/novelty/bench/run_live_bench.py --split test --seed 42`.

---

## Phase 3: real validation

**Goal:** evidence that LAIX decisions match what a knowledgeable person would choose on data the
team did not write.

- [x] **Build the validation harness** — `docs/06-research/03-validation/incident-replay.md`,
  `data/incident-replay/template.jsonl`, `data/vignette-study/v1/app/`,
  `scripts/novelty/incident-replay/preflight_incidents.py`, `scripts/novelty/incident-replay/ingest_incidents.py`,
  `scripts/novelty/incident-replay/analyze_incident_replay.py`, `data/vignette-study/v1/vignettes.json`
  (20 user-study vignettes), `scripts/novelty/vignette-study/analyze_vignette_study.py`,
  `scripts/novelty/vignette-study/serve_vignette_study.py`, and the consent/recruitment templates.

- [ ] **Run one external benchmark** — τ-bench for policy adherence, then ITBench for incident
  response. Protocol in [external benchmarks](02-evaluation/external-benchmarks.md).

- [x] **First external component run** — Sev1-Bench, all 20 scenarios. Baseline 0.800, LAIX
  guardrail 0.800, LAIX chooser 0.745 with one forbidden action; see
  [Sev1-Bench](02-evaluation/sev1-bench.md).

- [x] **Continuity benchmark v0** — 12 episodes, 60 decisions. Stateful `LiveCompositePlanner` 100%
  success, stateless `UtilityPlanner` 0% with 36 continuity errors; see
  [continuity benchmark](02-evaluation/continuity-benchmark.md).

- [x] **τ-bench baseline** — 10 retail tasks, DeepSeek V4 Flash, 9/10 passed (`pass^1 = 0.90`).
  The LAIX guardrail passed 10/10 on the same slice; a full retail policy adapter is next. See
  [τ-bench](02-evaluation/tau-bench.md).

- [ ] **Record the chosen option** — write one paragraph in
  `docs/06-research/03-validation/plan.md` §1 stating: which option (A, B or C) was chosen,
  why (data availability, feasibility, timeline), and the minimum sample size target. Do this
  before writing any ingestion or analysis code.

- [ ] **Pre-register the analysis plan** — before collecting any data, publish the analysis plan
  on the Open Science Framework (https://osf.io/prereg/). The plan must specify: the chosen
  option, the primary metric, the minimum sample size, the statistical test and the significance
  threshold (α = 0.05). Copy the OSF registration URL into `03-validation/plan.md` §1 under
  "Pre-registration". This prevents HARKing (hypothesizing after results are known) and is
  required by some venues.

**Choose exactly one of these three options before starting. Record the choice in
`docs/06-research/03-validation/plan.md` §1.**

### Option A — Incident replay

Replay historical incidents where a person already made a decision.

1. Find a source of historical incidents with a recorded human decision (support tickets, ops logs,
   approval records). Minimum: 200 raw incidents so that after filtering you have 40+ where LAIX
   and the human disagree.
2. Write an ingestion script in `scripts/novelty/incident-replay/ingest_incidents.py` that:
   - Reads the raw export.
   - Maps each incident to a `PlannerInput` JSON (using the case schema).
   - Strips all PII: names, emails, IPs, customer IDs, free-text that could identify a person.
   - Writes `data/incident-replay/output/anonymised.jsonl` (each line: one problem + human
     decision label).
3. Run `decide()` on each problem. Record LAIX verb and reason code.
4. Count: agreement rate, disagreement rate, discordant-pair list.
5. For the 40+ discordant pairs, run McNemar's test (H0: agreement is symmetric). Report χ²,
   p-value, 95% CI on the agreement rate.
6. Compute promise-keeping rate, irreversible-action rate and latency on the full set.
7. Write the method and results in `docs/06-research/03-validation/plan.md` §2 and §3.

### Option B — User study

Materials and protocol are ready: `data/vignette-study/v1/vignettes.json`,
`docs/06-research/03-validation/vignette-study.md` and `scripts/novelty/vignette-study/analyze_vignette_study.py`. Recruitment is external.

Recruit participants to judge LAIX decisions on vignette scenarios.

1. Write 20 vignettes in `data/vignette-study/v1/vignettes.json`. Each vignette has:
   - a situation description (plain English, no jargon);
   - 2–4 labelled options;
   - the LAIX decision (verb + rationale);
   - a human decision (collected from the participant).
2. Recruit at least 30 participants, each seeing all 20 vignettes. Counterbalance presentation
   order. Collect IRB approval or equivalent before starting.
3. For each vignette, record agreement (participant choice == LAIX choice) and a 5-point rating.
4. Use Fleiss' κ to measure inter-rater agreement. Use Wilcoxon signed-rank to compare ratings
   between LAIX decisions and the alternative.
5. Write the method (participants, procedure, materials, analysis) and results in
   `docs/06-research/03-validation/plan.md` §2 and §3.

### Option C — Deployment logging

Deploy LAIX in a real application, log decisions and collect outcomes.

1. Define the deployment domain and application in `docs/06-research/03-validation/plan.md` §1
   (one paragraph: what the app does, who the users are, what a "decision" means).
2. Add `OutcomeStore` logging to the application. Log every `decision_id`, chosen verb, and the
   measured outcome (a boolean or float) within 72 hours of the decision.
3. Collect at least 200 decisions (more if conflict cases are rare) over at least 30 days.
4. For the final analysis:
   - Compute outcome-weighted accuracy: fraction of decisions where the chosen verb matched
     the best outcome available.
   - Compute calibration (ECE and Brier) using `calibrate()` from the existing calibration module.
   - Use bootstrap (10 000 resamples) for 95% CIs on all metrics.
5. Write the method and results in `docs/06-research/03-validation/plan.md` §2 and §3.

### After the option is complete

- [ ] **Minimum check:** confirm 40+ discordant cases exist between LAIX and the human/ground-truth
  baseline. If fewer, the validation is underpowered — collect more data before writing up.
- [ ] **Write `docs/06-research/03-validation/plan.md` §4: Limitations** — list at minimum:
  - sample size and whether it was pre-registered;
  - domain coverage (which domains are excluded);
  - how the data was collected and by whom;
  - what could make the results not transfer to other domains;
  - any deviation from the pre-registered protocol.
- [ ] **Commit the anonymised data** (if legally permissible) or write a data-access statement in
  `03-validation/plan.md` §5 describing where the data is stored and how to request access.

**Deliverable:** `docs/06-research/03-validation/plan.md` filled with method, results and
limitations. At least one metric from outside the benchmark.

---

## Phase 4: paper

**Write in this order, and write each section when its evidence exists.**

- [x] **Claim–evidence map** — `02-evaluation/evidence-map.md`.
- [x] **Abstract (≤ 250 words)** — drafted in `04-publication/paper-draft.md`; validation pending.
- [x] **Related work** — drafted from `01-positioning/comparators.md` in `04-publication/paper-draft.md`.
- [x] **Formal model section** — drafted from `01-positioning/formal-model.md` in `04-publication/paper-draft.md`.
- [x] **Evaluation section** — drafted with the current tables in `04-publication/paper-draft.md`.
- [x] **Failure-case section** — drafted as the zero-failure limitation in `04-publication/paper-draft.md`.
- [ ] **Data availability statement** — needs the DOI and the validation data decision.
- [x] **Threats to validity** — drafted in `04-publication/paper-draft.md`.
- [x] **Reproducibility check** — `bash scripts/novelty/reproduce.sh` passes in CI.

**Deliverable:** a draft paper (or technical report) where every claim has a table row, every
table is reproducible with one command, and no sentence exceeds the evidence.

---

## Phase 5: artifact and release

- [x] **`CITATION.cff`** — created at the repo root using `cff-version: 1.2.0`.
  DOI is still pending the Zenodo deposit.

- [x] **Reproduction script** — created `scripts/novelty/reproduce.sh`.
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  python scripts/novelty/bench/validate_live_cases.py
  python scripts/novelty/bench/run_live_bench.py --split test --seed 42
  python scripts/novelty/analysis/analyze_results.py
  python scripts/novelty/bench/run_ablations.py --split test --seed 42
  python scripts/novelty/bench/summarize_results.py
  echo "All checks passed"
  ```
  `summarize_results.py` compares `metrics/summary.json` against the committed `metrics/baseline.json` and exits 1
  if any headline metric differs by more than 0.5 percentage points.

- [x] **CI job** — the Python CI job runs `bash scripts/novelty/reproduce.sh` on every push.

- [x] **Artifact manifest** — `docs/06-research/04-publication/artifact-manifest.md` lists the files for
  the release. DOI and tag are still pending.

- [ ] **Tag the release** - once the reproduction script passes on a fresh clone:
  ```bash
  git tag -a v1.0.0 -m "LAIX 1.0.0 — live benchmark release"
  git push origin v1.0.0
  ```
  The tag version must match `CITATION.cff`.

- [ ] **Update `CHANGELOG.md`** - an Unreleased entry is already added; the tagged release entry
  and DOI remain. The entry
  must include: the date, a one-paragraph summary of what the release adds (live benchmark,
  120 cases, bootstrap CIs, reproduction script), the Zenodo DOI (add it after deposit), and
  the command to reproduce the main table. Format must match existing entries in `CHANGELOG.md`.

- [ ] **Zenodo deposit** — connect the GitHub repo to Zenodo (https://zenodo.org/account/settings/github/).
  Trigger the deposit by pushing the `v1.0.0` tag. Zenodo will auto-generate the DOI. Copy the
  DOI into `CITATION.cff` under `doi:` and commit.

- [ ] **Publish the benchmark** — in the Zenodo deposit include:
  - `benchmarks/live/v1/dev.json`
  - `benchmarks/live/v1/test.json`
  - `benchmarks/live/v1/schema.json`
  - `results/live-decision-benchmark/metrics/summary.json`
  Do **not** include `adversarial.json` in the public deposit (keep it private to
  prevent gaming).

**Deliverable:** a tagged release, a Zenodo DOI, a CI job that keeps the main table green.

---

## Phase 6: external review

- [x] **Create `docs/06-research/04-publication/review-log.md`** — template created; fill it during review.
  It is a table with columns: `date`, `reviewer`, `comment summary`, `action taken`,
  `metric before`, `metric after`. Every change made in response to a reviewer must have a row.
  The file is referenced by the reviewer response protocol below.

- [ ] **Submit to a venue** — pick one target from this list (in priority order):
  1. A systems workshop at NeurIPS, ICML or ICLR (deadline usually June–August; check
     `https://aideadlin.es` for the current year).
  2. AAMAS (deadline usually November).
  3. ICAART (deadline usually October).
  Submit the paper from Phase 4. Include the Zenodo DOI as the artifact link.

- [ ] **Reviewer response protocol** — for each reviewer comment:
  - If a reviewer asks for a new experiment: run it, add the result to `results/`, update the
    paper table with the new number.
  - If a reviewer challenges a claim: either (a) add more evidence (a new metric, an additional
    split), or (b) narrow the claim. Never expand a claim in a rebuttal.
  - If a reviewer finds a bug in the code: fix it, re-run the benchmark, update the numbers, and
    describe the fix in the camera-ready changelog.
  - Record all changes in `docs/06-research/04-publication/review-log.md` with the reviewer comment, the
    action taken and the resulting number change.

- [ ] **Independent replication** — share `scripts/novelty/reproduce.sh` and
  `benchmarks/live/v1/test.json` with one person outside the team. Ask them to:
  1. Clone the repo on a machine they control.
  2. Run `bash scripts/novelty/reproduce.sh`.
  3. Report whether the main table in the paper matches their output within 0.5 pp.
  Record the outcome (pass/fail and their machine details) in `docs/06-research/04-publication/review-log.md`.

- [ ] **Final claim update** — after acceptance, update three places with the validated numbers:
  1. `docs/06-research/README.md` §1 — replace the interim claim with the final
     peer-reviewed numbers (accuracy, CI, effect size).
  2. `README.md` "Why LAIX" section — replace "pending validation" language with the final numbers.
  3. `01-positioning/prior-art.md` introduction — add the venue and DOI as the citation anchor.

- [ ] **Close the open decisions** — `docs/06-research/README.md` §5 lists six open
  decisions. After the paper is accepted, add a one-sentence answer to each one directly in that
  file, beneath the question. Keep the questions as a record of what was uncertain. The six questions are:
  1. Which domain for the real validation? → state the domain used.
  2. Deployment, incident replay or user study? → state the option chosen.
  3. Which venue and paper length? → state the venue, paper length and acceptance status.
  4. Public benchmark or private evaluation set? → state what was published and why.
  5. Which claims are safe if the benchmark gives mixed results? → state the fall-back claim
     actually used in the submitted paper.
  6. Who is the independent reviewer or replication partner? → record name or handle (can be
     anonymous) and the outcome (pass/fail, date).

---

## What "next small step" means

Tasks marked as a **next small step** can be done without any external data, service or user study.
They are pure writing or code over the existing implementation.

The first task in Phase 2 (writing the 120 cases) is a next small step: it requires only the case
schema and the existing `default_cases()` as examples, no external data.

The first task in Phase 3 requires a decision (which option to pursue) before anything else can
start. Make that decision before writing any code.
