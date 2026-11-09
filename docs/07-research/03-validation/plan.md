# Real-world validation

Synthetic cases need an external check. This page defines the study that shows the decision layer works outside the
repository tests.

## Validation options

Synthetic cases need an external check. Choose one:

### Option A: incident or support replay

- harness: `scripts/novelty/incident-replay/ingest_incidents.py` and `scripts/novelty/incident-replay/analyze_incident_replay.py`;
- take historical events;
- replay through LAIX and the baseline;
- compare decisions against what a human did;
- report disagreements and their costs.

### Option B: user study

- materials: `data/vignette-study/v1/vignettes.json` (20 vignettes);
- protocol: `docs/07-research/03-validation/vignette-study.md`;
- analysis: `scripts/novelty/vignette-study/analyze_vignette_study.py`;
- ask operators to judge decisions from LAIX and a baseline;
- blind the source;
- measure acceptance, perceived timeliness, trust and workload;
- include a sample-size justification.

### Option C: deployment or pilot

- one host application;
- two to four weeks;
- log decisions, approvals, executions and outcomes;
- measures: promise keeping, irreversible actions, attention spend, missed deadlines,
  undo rate, acceptance rate.

For all options, document consent, privacy, data minimisation and retention. Keep personal data out
of the public artifact.

### Acceptance criteria

- At least one validation outside the repository test suite.
- A clear method section and a limitations section.
- Raw data is either public or its absence is justified.

## Study record

Fill this in before collecting data.

### 1. Chosen option

- Option:
- Why this option:
- Data source / participants:
- Minimum sample size:
- Owner:
- Start and end date:

### 2. Pre-registration

- Registration URL:
- Primary metric:
- Secondary metrics:
- Statistical test:
- Significance threshold:
- Stopping rule:
- Deviations (after the study):

### 3. Method

- How the data was collected:
- How it was anonymised:
- Inclusion and exclusion rules:
- How LAIX and the baselines were run:
- Environment and commit:

### 4. Results

- Cases collected:
- Discordant cases:
- Agreement rate and 95% CI:
- Promise keeping, irreversible actions, attention spend:
- Comparison with glue and utility:
- Unexpected results:

### 5. Limitations

- Sample size and power:
- Domain coverage:
- Collection bias:
- Transferability:
- Deviations from pre-registration:

### 6. Data access

- Public location or DOI:
- Access procedure if private:
- Reason it cannot be published:

Harness commands:

```bash
python scripts/novelty/incident-replay/ingest_incidents.py --input data/incident-replay/raw/incidents.jsonl
python scripts/novelty/incident-replay/analyze_incident_replay.py
```
