# Real-world validation

Synthetic cases are not enough. This page defines the study that shows the layer works outside the
repository tests.

## Validation options

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
