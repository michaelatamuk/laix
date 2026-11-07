# Sev1-Bench external run

Status: first external component run, 20 of 20 scenarios. This is not a substitute for real
incident replay.

[Sev1-Bench](https://github.com/edgedelta/sev1-bench) is a deterministic benchmark built from
public SRE postmortems and synthetic harness scenarios. Each scenario supplies frozen observability
fixtures, a brief and a hidden rubric. The scorer is a pure function of the final answer and the task.

## Setup

- Host model: `deepseek-v4-flash`, temperature 0, `reasoning_effort` low.
- Input: the scenario brief and frozen fixtures only. The model never sees the rubric.
- Scoring: an exact port of the public scorer. Weights are 0.5 root cause, 0.3 remediation and
  0.2 no forbidden action; pass threshold 0.7.
- Sample: all 20 scenarios.

Three variants were scored from the same model output:

| Variant | What it does |
|---|---|
| **Baseline** | Uses the model's top remediation. |
| **LAIX chooser** | `LiveDecisionEngine` always chooses among the four candidates. |
| **LAIX guardrail** | Keeps the model's top remediation when it is already safe; overrides only destructive, approval-required or high-risk choices. |

## Results

| Variant | Mean | Passed | Root cause | Remediation | Forbidden |
|---|---:|---:|---:|---:|---:|
| Baseline | **0.800** | 15/20 | 15/20 | 15/20 | 0/20 |
| LAIX chooser | 0.745 | 14/20 | 14/20 | 13/20 | 1/20 |
| LAIX guardrail | **0.800** | 15/20 | 15/20 | 15/20 | 0/20 |

By category:

| Category | n | Baseline | Chooser | Guardrail |
|---|---:|---:|---:|---:|
| RCA | 12 | 0.800 | 0.775 | 0.800 |
| Noise rejection | 5 | 0.740 | 0.740 | 0.740 |
| Cascade | 2 | 0.850 | 0.850 | 0.850 |
| Triage | 1 | 1.000 | 0.200 | 1.000 |

## Finding

On this benchmark, the model's top remediation was already safe in every scenario. LAIX therefore
had no scored upside: accuracy, calibration, approval and continuity are not measured by this
benchmark.

The **chooser** integration regressed on two scenarios. On multi-incident triage it selected a
correct first action but dropped the wider triage context. On the large-tool-result scenario it
introduced one forbidden action and lost the remediation score. The **guardrail** integration kept
the model's answer when it was already safe and avoided both regressions.

This is a useful negative result: a runtime that always replaces the model's choice can make a
single-turn benchmark worse. The safe integration is to use LAIX as a guardrail and decision
contract, not as a second diagnostician.

## Model robustness

| Model | Scenarios | Baseline | Guardrail | Chooser | Forbidden (baseline / guardrail) |
|---|---:|---:|---:|---:|---:|
| DeepSeek V4 Flash | 20 | **0.800** | **0.800** | 0.745 | 0 / 0 |
| DeepSeek V4 Pro | 16 | **0.656** | **0.656** | 0.637 | 1 / 0 |

The V4 Pro run attempted 18 scenarios; two failed JSON parsing (`background-batch`,
`multi-symptom`) and are excluded. The heavy scenarios were not run with V4 Pro.

V4 Pro is not uniformly better than Flash on this benchmark; model choice changes individual
scenarios. The guardrail preserved the baseline mean in both models. On V4 Pro it removed the one
forbidden recommendation (`haystack`) without losing score. The chooser still regressed on
`s3-typo` for V4 Pro.

The full V4 Pro summary is in `pro-summary.json`.

## Reproduce

```bash
git clone https://github.com/edgedelta/sev1-bench.git
pip install -r results/external/sev1-bench/requirements.txt
export SEV1_BENCH=/path/to/sev1-bench
export DEEPSEEK_API_KEY=...
python results/external/sev1-bench/run.py
python results/external/sev1-bench/summary.py
```

The raw rows, including per-scenario candidates and all three scores, are in `results.json`.

## Limitations

- One model, one deterministic run; no variance estimate.
- Fixtures are supplied directly rather than through the published tool servers. The scorer only
  reads the final answer and forbidden tool calls, so the score is unaffected, but the harness
  differs from the published smolagents and Edge Delta runs.
- The benchmark does not model approval state. LAIX's escalation path is included in the final
  answer as the route to the approved remediation.
- The sample is small. Treat this as a component signal, not a generalisation claim.
