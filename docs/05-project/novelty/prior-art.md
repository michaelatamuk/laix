# Prior art and comparison

Establish what already exists, what the closest systems cover and what remains open. This page is
the source for the related-work section and the comparison protocol.

## 1. Prior-art analysis

### Deliverable

This page should contain:

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

## 2. Comparison targets and fair comparison protocol

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

## 3. Finding comparators when you do not know the field

You do not need to know the field before starting. Use a repeatable search and triage process.

### Principle: compare on the task, not the label

Do not search for "systems like LAIX". Search for systems that solve pieces of the same task:

> Given a live request, choose one action under promises, execution risk, attention limits and audit.

Every candidate should answer at least one of these questions:

- Does it make a decision, or only execute one?
- Does it represent promises or obligations?
- Does it model execution risk, approval or recovery?
- Does it manage human attention or interruption?
- Does it preserve timing, revision or replay?
- Does it calibrate confidence or learn from outcomes?
- Does it produce an auditable decision trail?

### The comparison ladder

Start close, then widen:

1. **Internal baselines** — no literature search needed: first option, highest benefit,
   utility-only, single-concern planners, ablations.
2. **Direct competitors** — systems that claim to make live or agent decisions.
3. **Adjacent systems** — systems that own one part: orchestration, durable execution,
   alerting, planning, calibration.
4. **Academic lines** — one mechanism each: commitments, interruption cost, POMDP planning,
   calibration, sagas.
5. **Operational alternatives** — build it yourself with glue code, or use a general workflow
   engine.

### Search protocol

Use the same protocol for every category and keep a search log.

Sources:

- Google Scholar, Semantic Scholar and arXiv;
- ACM Digital Library, IEEE Xplore, AAAI, AAMAS, CHI, IUI and HHAI proceedings;
- GitHub topics and search: `ai-agents`, `workflow-engine`, `decision-engine`,
  `human-in-the-loop`, `durable-execution`, `policy-engine`;
- official documentation and changelogs of candidate systems;
- citation chaining: take two or three survey papers and follow both backward and forward;
- benchmark and dataset papers in the same area.

Search strings to try:

```text
"live decision" AI system
"decision layer" agent
"decision engine" audit approval
"human-in-the-loop" agent interrupt approval
"commitment-based" multi-agent protocol
"social commitments" agent
"interruption budget" notification
"notification fatigue" scheduling
"durable execution" approval workflow
"compensating transaction" saga workflow
"policy engine" decision audit
"calibration" decision confidence
"decision calibration" accuracy
"real-time decision support" uncertainty
```

For each candidate, record:

- name and version;
- category;
- task overlap;
- concern overlap;
- whether it can be run locally;
- evidence quality;
- maintenance status;
- source link;
- last checked date.

### Inclusion and exclusion

Include a candidate when at least two are true:

- it makes or gates a decision;
- it represents commitments, approvals or execution state;
- it manages attention or interruption;
- it has audit, replay or recovery;
- it reports decision-quality or calibration numbers.

Exclude a candidate when:

- it is only a model or a model-serving layer;
- it is only a UI toolkit;
- it is only a storage or queue system;
- it cannot be described without a specific vendor domain.

### Triage score

Score each candidate from 0 to 3:

| Dimension | 0 | 3 |
|---|---|---|
| Task overlap | different task | same live decision task |
| Concern overlap | one unrelated concern | commitments, risk, attention and audit |
| Runnability | closed or undocumented | runnable adapter with docs |
| Evidence quality | marketing claim | benchmark or peer-reviewed evidence |
| Maintenance | abandoned | active releases |

Keep the top two per category. Stop when adding a candidate no longer changes the matrix.

### Starter shortlist

Verify every entry and record the version before using it.

| Candidate | Category | Why it is relevant | Compare on |
|---|---|---|---|
| LangGraph | agent orchestration | stateful graph, interrupts, human approval, checkpoints | capability, latency, glue code |
| AutoGen | multi-agent orchestration | conversation and human input | capability, orchestration overhead |
| CrewAI | agent orchestration | role-based process and human input | capability, glue code |
| Semantic Kernel | orchestration and functions | planners, functions and filters | capability, integration effort |
| Temporal | durable execution | retries, timers, signals, compensation | recovery, audit, operational cost |
| Airflow | workflow orchestration | DAG scheduling and retries | operational cost, audit |
| Prefect | workflow orchestration | flows, retries and observability | operational cost |
| Netflix Conductor | workflow orchestration | durable workflows and task state | recovery, audit |
| Camunda | BPMN workflow | approvals, compensation, audit | approval and compensation semantics |
| PagerDuty | alerting and on-call | escalation, routing, on-call policy | attention and escalation |
| Opsgenie | alerting and on-call | routing and escalation | attention and escalation |
| AI-Toolbox or pomdp-solve | planning | MDP/POMDP decision quality | decision quality on the same model |
| scikit-learn calibration | calibration | reliability curves, ECE, Brier | calibration numbers |
| Commitment-based multi-agent systems | academic | promises, violations, dependencies | formal commitment semantics |
| Mixed-initiative and interruption research | academic | interruption cost and timing | attention model and user study |
| Saga and compensation literature | academic | compensating transactions | recovery semantics |

### If no direct comparator exists

That is a possible result, but it must be earned:

1. Run the search protocol and keep the log.
2. Show the closest system in each category.
3. Explain the missing combination.
4. Compare against the strongest component or a hand-built glue baseline.
5. Say "we found no system that ..." with the search date and inclusion criteria.

Do not write "no one does this" without the log.

### Deliverable

Create `comparators.md` with:

- the search log;
- the inclusion and exclusion decisions;
- the triage scores;
- one paragraph per final comparator;
- the adapter plan or the reason it cannot be run;
- the final comparison table.

### Acceptance criteria

- The search is reproducible from the log.
- At least two categories have a runnable comparator.
- The final set includes one direct or adjacent competitor, one planning or calibration
  comparator, and one academic line.
- The paper can explain why each comparator is fair.
