# Sev1-Bench external run

Status: first external component run, 18 of 20 scenarios. This is not a substitute for real
incident replay.

[Sev1-Bench](https://github.com/edgedelta/sev1-bench) is a deterministic benchmark built from
public SRE postmortems and synthetic harness scenarios. Each scenario supplies frozen observability
fixtures, a brief and a hidden rubric. The scorer is a pure function of the final answer and the task.

## Setup

- Host model: `deepseek-v4-flash`, temperature 0, `reasoning_effort` low.
- Input: the scenario brief and frozen fixtures only. The model never sees the rubric.
- Scoring: an exact port of the public scorer. Weights are 0.5 root cause, 0.3 remediation and
  0.2 no forbidden action; pass threshold 0.7.
- Sample: 18 of 20 scenarios. The two fixtures above 100 KB were excluded from this first run
  because they test tool-result handling rather than decision quality.

Three variants were scored from the same model output:

| Variant | What it does |
|---|---|
| **Baseline** | Uses the model's top remediation. |
| **LAIX chooser** | `LiveDecisionEngine` always chooses among the four candidates. |
| **LAIX guardrail** | Keeps the model's top remediation when it is already safe; overrides only destructive, approval-required or high-risk choices. |

## Results

| Variant | Mean | Passed | Root cause | Remediation | Forbidden |
|---|---:|---:|---:|---:|---:|
| Baseline | **0.778** | 13/18 | 13/18 | 13/18 | 0/18 |
| LAIX chooser | 0.733 | 12/18 | 12/18 | 12/18 | 0/18 |
| LAIX guardrail | **0.778** | 13/18 | 13/18 | 13/18 | 0/18 |

By category:

| Category | n | Baseline | Chooser | Guardrail |
|---|---:|---:|---:|---:|
| RCA | 10 | 0.760 | 0.760 | 0.760 |
| Noise rejection | 5 | 0.740 | 0.740 | 0.740 |
| Cascade | 2 | 0.850 | 0.850 | 0.850 |
| Triage | 1 | 1.000 | 0.200 | 1.000 |

## Finding

On this benchmark, the model's top remediation was already safe in every scenario. LAIX therefore
had no scored upside: accuracy, calibration, approval and continuity are not measured by this
benchmark.

The **chooser** integration regressed on the multi-incident triage case. It selected a correct
first action but dropped the wider triage context, so the final answer failed the rubric. The
**guardrail** integration kept the model's full answer and avoided the regression.

This is a useful negative result: a runtime that always replaces the model's choice can make a
single-turn benchmark worse. The safe integration is to use LAIX as a guardrail and decision
contract, not as a second diagnostician.

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
- 18 of 20 scenarios.
- Fixtures are supplied directly rather than through the published tool servers. The scorer only
  reads the final answer and forbidden tool calls, so the score is unaffected, but the harness
  differs from the published smolagents and Edge Delta runs.
- The benchmark does not model approval state. LAIX's escalation path is included in the final
  answer as the route to the approved remediation.
- The sample is small. Treat this as a component signal, not a generalisation claim.
