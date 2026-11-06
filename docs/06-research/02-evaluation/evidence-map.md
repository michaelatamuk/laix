# Claim–evidence map

Status: repository-side evidence is complete. External validation and peer review are still pending.
Every number below is reproducible from `results/live-decision-benchmark/` and `bash scripts/novelty/reproduce.sh`.

## Current claims

| Claim | Metric | Value | Source | Status |
|---|---|---|---:|---|---|
| The integration is accurate on the frozen test split | accuracy | 100% (30/30) | `results/live-decision-benchmark/metrics/summary.json` | measured |
| It beats the best single-concern planner | accuracy delta | +30 pp (100% vs 70%) | `metrics/summary.json` | measured |
| It beats a hand-built glue baseline | accuracy delta | +6.7 pp (100% vs 93.3%), p = 0.48 | `metrics/significance.json` | measured, not significant |
| It wins when concerns conflict | conflict accuracy | 100% (6/6) | `metrics/summary.json` | measured |
| It wins against every single-concern planner | McNemar p | p ≤ 0.008 for every single-concern planner | `metrics/significance.json` | measured |
| It wins against hand-built glue code | McNemar p | p = 0.48 | `metrics/significance.json` | **not significant** |
| It keeps promises | promise-keeping rate | 100% (vs 0% utility-only) | `metrics/summary.json` | measured |
| It avoids irreversible actions | irreversible-action rate | 0% (vs 23.3% highest-benefit) | `metrics/summary.json` | measured |
| It respects the attention budget | budget-violation rate | 0% (vs 70% highest-benefit) | `metrics/summary.json` | measured |
| The integration is doing real work | ablation delta | full 100%; no commitment 70%; no execution 83.3%; no attention 96.7% | `results/live-decision-benchmark/ablations/results.json` | measured |
| The case files are valid | schema validation | 120/120 valid, unique ids | `scripts/novelty/bench/validate_live_cases.py` | tested |
| The live path is fast enough | p95 latency | under 2 ms on the test split | `metrics/summary.json` | measured |
| The model is deterministic | replay equality | 100% across the invariant suite | `tests/core/test_invariants.py` | tested |
| The contract is stable | invariant tests | 17/17 | `tests/core/test_invariants.py` | tested |
| Python and TypeScript agree | conformance + live-bench action parity | 24/24 conformance; 210/210 live actions; 172 TS tests | CI | tested |
| The layer is auditable | trace and receipt tests | I6–I9 pass | `tests/core/test_invariants.py` | tested |
| LangGraph can host the same decision | operational adapter | 120 decisions, 0 interrupts, 6-7 ms mean, 110 glue lines | `results/live-decision-benchmark/comparison/external-systems.json` | measured (operational only) |
| The audit answers EU PLD questions | field mapping | `verb`, `reason_code`, `policy_version`, `decision_id`, `trace_id`, `created_at` | `eu-liability.md` | documented |

## Claims that still need evidence

| Claim | Missing evidence | Next step |
|---|---|---|
| The integration beats an external system | runnable adapter comparison | Phase 2 external comparison in `../01-positioning/prior-art.md` |
| The layer works in a real domain | deployment, incident replay or user study | Phase 3 in `checklist.md` |
| The results generalise | independent replication | Phase 6 in `checklist.md` |
| The paper's claims are accepted | peer review | Phase 6 in `checklist.md` |

## Rules

- Every row needs a source.
- A row marked "measured" must be reproducible from the listed command or file.
- A row marked "tested" must fail if the code regresses.
- A row marked "documented" is an argument and is labelled as such.
- Promote a claim from "measured" to "general" only after external validation.
