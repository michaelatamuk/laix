# Novelty checklist

Work through the phases in order. Do not move to the paper until the evidence exists.

## Phased checklist

### Phase 0: claim and prior art

- [ ] Write the one-paragraph claim.
- [ ] Write scope and non-goals.
- [ ] Build the prior-art matrix.
- [ ] Write the closest-prior-work paragraph.
- [ ] Rewrite the claim after the matrix.
- Deliverable: `prior-art.md`.
- Done when an external reader can see exactly what is new and what is not.

### Phase 1: formal model and invariants

- [ ] Define the problem, score and feasibility.
- [ ] Define revision and receipt state machines.
- [ ] Write invariants I1-I10.
- [ ] Add property tests.
- Deliverable: `formal-model.md` and tests.
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
