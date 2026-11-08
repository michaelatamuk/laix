# Pre-registration template

Use this before an external run. The point is to decide the analysis before seeing the result, so a
positive result is credible and a negative result is still publishable.

## 1. Question

- What decision problem does the run test?
- What is the unit of analysis: one decision, one episode or one task?
- What is explicitly out of scope?

## 2. Hypotheses

State one primary hypothesis and any secondary hypotheses.

- Primary: ...
- Secondary: ...

A useful primary hypothesis names the comparator and the metric, for example: *`LiveCompositePlanner`
has a higher conflict-case accuracy than the hand-built glue baseline on the frozen test split.*

## 3. Data

- Source and owner of the data.
- Collection window and inclusion rules.
- Privacy, consent and PII handling.
- Split sizes: dev, test and adversarial.
- Whether the test split is frozen before the run.
- Whether any case was seen during development.

External acceptance target: at least 100 cases per decision class where the class applies, and at
least two external baselines.

## 4. Baselines

- The current process or hand-built glue.
- At least one single-concern planner.
- At least one external system where the task is comparable.

Report which baselines are runnable and which are documented only.

## 5. Metrics

Primary:

- accuracy or task success;
- promise keeping;
- irreversible-action rate;
- human-attention-budget violations;
- p95 decision latency.

Secondary:

- approval correctness;
- continuity errors;
- audit completeness;
- recovery and rollback;
- cost per decision;
- integration effort.

## 6. Analysis plan

- Paired or unpaired test, and why.
- Confidence interval method.
- Effect size.
- Handling of missing or inconclusive cases.
- Subgroup analyses, declared in advance.
- Stopping rule and whether interim results are allowed.

For paired binary outcomes, McNemar and a paired bootstrap are the default. Report the discordant
pairs, not only the p-value.

## 7. Threats

- Leakage between dev and test.
- Cases authored by the same team that built the planner.
- A weak baseline.
- A saturated benchmark.
- A single trial with high variance.
- A latency measurement taken on a different machine.

## 8. Result handling

- Publish negative and null results.
- Keep the raw result JSON and the analysis command.
- Record the package, policy and vector versions.
- State whether the result generalises beyond the corpus.
- Do not promote a claim to `general` without independent replication.

## 9. Artifact

- Repository commit and tag.
- Reproduction command.
- Expected runtime and dependencies.
- Data availability and access conditions.

## 10. Independent replication

- Who can run it.
- What they need.
- What counts as a successful replication.
- Where the result will be published.

## Related

- [Benchmark](benchmark.md) - the internal protocol and threats.
- [Evidence map](evidence-map.md) - what is measured and what is missing.
- [Adoption plan](../../05-project/04-direction/02-adoption-plan.md) - the external acceptance criteria.
