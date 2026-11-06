# Paper and artifact

Write the paper only after the evidence exists. This page covers reproducibility, the artifact, the
paper outline and the venues. The current draft is in [paper-draft.md](paper-draft.md); it is marked
validation-pending and is not submittable yet.

## 1. Reproducibility and artifact

Already present:

- `CITATION.cff`
- `scripts/novelty/reproduce.sh`
- a CI job that runs the live benchmark, analysis and ablations
- `results/live-decision-benchmark/` with the reported run
- [artifact-manifest.md](artifact-manifest.md)

Still pending:

- `LICENSE` reference in the paper
- a pinned environment file
- a versioned release and DOI
- the final paper draft after real validation

Acceptance criteria:

- A fresh clone can reproduce the main table.
- The paper states the commit hash and package versions.
- The artifact includes Python and TypeScript conformance cases.
- No secret or personal data is required.

## 2. Paper and dissemination

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

Create a table in the paper and in `../02-evaluation/evidence-map.md`:

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
