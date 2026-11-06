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
