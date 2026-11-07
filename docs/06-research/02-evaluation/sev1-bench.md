# Sev1-Bench

Status: first external component run. Results are reported below; the run is not a substitute for
real incident replay.

[Sev1-Bench](https://github.com/edgedelta/sev1-bench) is a deterministic benchmark built from public
SRE postmortems and synthetic harness scenarios. Each scenario ships with frozen observability
fixtures, a brief and a rubric. The scorer is a pure function of the final answer and the task, so a
result needs no live cluster and no API key to verify.

## Why this benchmark

- It is built from real incidents: GitLab `rm -rf`, Cloudflare regex, S3 typo, GitHub partition,
  Heroku failover and others.
- It scores both diagnosis and remediation, including forbidden actions.
- It is deterministic and public, so the baseline and LAIX runs can be re-scored.
- It tests the incident-response case named in the validation plan.

## Experiment

- **Host model:** `deepseek-v4-flash`, temperature 0, `reasoning_effort` low.
- **Input:** the scenario brief and frozen fixtures only. The model never sees the rubric.
- **Baseline:** the model's own top remediation.
- **LAIX chooser:** the model proposes four remediation candidates with expected benefit,
  reversibility, risk, approval need and destructiveness. `LiveDecisionEngine` always chooses among
  them. When it chooses escalation or further investigation, the final answer includes the approved
  remediation path.
- **LAIX guardrail:** keep the model's top remediation when it is already safe; override only
  destructive, approval-required or high-risk choices.
- **Scoring:** an exact port of the public scorer. Weights: 0.5 root cause, 0.3 remediation,
  0.2 no forbidden action. Pass threshold 0.7.
- **Sample:** all 20 scenarios.

## Results

The summary is generated from
[`results/external/sev1-bench/results.json`](../../../results/external/sev1-bench/results.json).

| Variant | Mean score | Passed | Root cause | Remediation | Forbidden |
|---|---:|---:|---:|---:|---:|
| DeepSeek baseline | **0.800** | 15/20 | 15/20 | 15/20 | 0/20 |
| DeepSeek + LAIX chooser | 0.745 | 14/20 | 14/20 | 13/20 | 1/20 |
| DeepSeek + LAIX guardrail | **0.800** | 15/20 | 15/20 | 15/20 | 0/20 |

By category:

| Category | n | Baseline | Chooser | Guardrail |
|---|---:|---:|---:|---:|
| RCA | 12 | 0.800 | 0.775 | 0.800 |
| Noise rejection | 5 | 0.740 | 0.740 | 0.740 |
| Cascade | 2 | 0.850 | 0.850 | 0.850 |
| Triage | 1 | 1.000 | 0.200 | 1.000 |

The model's top remediation was already safe in every scenario, so LAIX had no scored upside.
The **chooser** variant regressed on multi-incident triage and on large-tool-result; the latter
introduced one forbidden action and lost the remediation score. The **guardrail** variant kept the
model's answer when it was already safe and avoided both regressions.

This is a useful negative result. A runtime that always replaces the model's choice can make a
single-turn benchmark worse. The safe integration is to use LAIX as a guardrail and decision
contract, not as a second diagnostician.

See the full method and per-scenario rows in
[`results/external/sev1-bench/`](../../../results/external/sev1-bench/README.md).

## Limitations

- One model, one deterministic run; no variance estimate.
- Fixtures are supplied directly, not through the published tool servers. The scorer only reads the
  final answer and forbidden tool calls, so this does not change the score, but it is a different
  harness from the published smolagents/Edge Delta runs.
- The benchmark does not model approval state. LAIX's escalation step is included in the final
  answer as the path to the approved remediation.
- The sample is small. The result is a component signal, not a generalisation claim.

## Reproduce

The run script and raw result rows are in `results/external/sev1-bench/`.
