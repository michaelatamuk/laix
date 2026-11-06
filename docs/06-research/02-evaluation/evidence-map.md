# Claim–evidence map

Status: repository-side evidence is complete. External validation and peer review are still pending.

Every measured number is reproducible from
[`results/live-decision-benchmark/`](../../../results/live-decision-benchmark/) and
`bash scripts/novelty/reproduce.sh`.

## Headline results

| Claim | Result | Status |
|---|---|---|
| Accuracy, frozen test split | **100%** (30/30) | measured |
| Conflict accuracy | **100%** (6/6) | measured |
| Best single-concern planner | **+30 pp** (100% vs 70%) | measured |
| Hand-built glue baseline | **+6.7 pp** (100% vs 93.3%), p = 0.48 | not significant |
| Ablation: full vs no commitment | **100%** vs **70%** | measured |
| Ablation: full vs no execution | **100%** vs **83.3%** | measured |
| Ablation: full vs no attention | **100%** vs **96.7%** | measured |

The glue comparison is the honest caveat: the gain is real on this corpus, but the 95% confidence
interval includes zero and p = 0.48 on 30 cases. The advantage over every single-concern planner is
significant (McNemar p ≤ 0.008 for each).

## Safety and promise keeping

| Check | LAIX | Comparator | Status |
|---|---:|---:|---|
| Promise-keeping rate | **100%** | 0% (utility-only) | measured |
| Irreversible-action rate | **0%** | 23.3% (highest-benefit) | measured |
| Attention-budget violation rate | **0%** | 70% (highest-benefit) | measured |
| p95 latency, test split | **< 2 ms** | — | measured |

## Contract and parity

| Check | Result | Evidence | Status |
|---|---|---|---|
| Case schema | 120/120 valid; unique ids | [validator](../../../scripts/novelty/bench/validate_live_cases.py) | tested |
| Determinism | 100% replay equality | [invariants](../../../packages/python/laix/tests/core/test_invariants.py) | tested |
| Contract invariants | 17/17 | [invariants](../../../packages/python/laix/tests/core/test_invariants.py) | tested |
| Python/TypeScript parity | 24/24 conformance; 210/210 live actions; 172 TS tests | CI | tested |
| Audit trail | I6–I9 pass | [invariants](../../../packages/python/laix/tests/core/test_invariants.py) | tested |
| LangGraph host | 120 decisions; 0 interrupts; 6–7 ms mean; 110 glue lines | [comparison](../../../results/live-decision-benchmark/comparison/external-systems.json) | measured (operational) |
| EU PLD audit fields | see below | [EU PLD](../05-governance/eu-liability.md) | documented |

### EU PLD audit fields

| Question | Field |
|---|---|
| What was decided? | `verb` |
| Why? | `reason_code` |
| Under which policy? | `policy_version` |
| Which decision? | `decision_id` |
| Which trace? | `trace_id` |
| When? | `created_at` |

## Still needs evidence

| Claim | Missing evidence | Next step |
|---|---|---|
| The integration beats an external system | Runnable adapter comparison | Phase 2 in [prior art](../01-positioning/prior-art.md) |
| The layer works in a real domain | Deployment, incident replay or user study | Phase 3 in [checklist](../checklist.md) |
| The results generalise | Independent replication | Phase 6 in [checklist](../checklist.md) |
| The paper's claims are accepted | Peer review | Phase 6 in [checklist](../checklist.md) |

## Evidence index

| Evidence | What it shows |
|---|---|
| [Benchmark summary](../../../results/live-decision-benchmark/metrics/summary.json) | Accuracy, conflict, promises, safety, budget and latency. |
| [Significance tests](../../../results/live-decision-benchmark/metrics/significance.json) | McNemar tests, confidence intervals and effect sizes. |
| [Ablations](../../../results/live-decision-benchmark/ablations/results.json) | Full integration vs removing one concern. |
| [External comparison](../../../results/live-decision-benchmark/comparison/external-systems.json) | LangGraph adapter results. |
| [Case validator](../../../scripts/novelty/bench/validate_live_cases.py) | Schema and id checks. |
| [Invariant tests](../../../packages/python/laix/tests/core/test_invariants.py) | Determinism, contract and audit invariants. |
| [EU PLD mapping](../05-governance/eu-liability.md) | Audit fields for liability questions. |

## Rules

- Every row needs a source.
- `measured` is reproducible from the listed file or command.
- `tested` fails if the code regresses.
- `documented` is an argument, not a measurement.
- Promote a claim to `general` only after external validation.
