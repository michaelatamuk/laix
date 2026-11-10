# Migration and deprecation

LAIX is pre-1.0. Treat every minor release as potentially breaking, even when the package
version only moves by a small amount. This page is the upgrade path; the version axes are in
[Versioning](01-versioning.md).

## Before an upgrade

1. Read the release section in [CHANGELOG.md](../../../CHANGELOG.md).
2. Note the current package, record-schema and rule-set versions.
3. Capture a baseline: test results, bench summary and one representative decision record.
4. Run the current test suite before changing anything, so a failure is attributable.

## Upgrade steps

1. Update the Python and TypeScript packages together.
2. Run the full checks:

   ```powershell
   cd packages/python/laix
   python -m pytest -q
   python -m ruff check .

   cd packages/typescript/laix
   npm run typecheck
   npm test
   npm run conformance
   npm run live-bench
   ```

3. If the record schema changed, regenerate `laix-v1.schema.json` from the package and
   update the stored-record schema.
4. Replay one representative decision and compare the verb, reason code, action and score
   breakdown with the baseline.
5. Run the live benchmark and compare the summary with the committed baseline:

   ```powershell
   bash scripts/novelty/reproduce.sh
   ```

6. Update pins in the host, CI and deployment manifests.
7. Keep the previous package version available for rollback until the new version is stable.

## 0.12.0: `laix.core` is now `laix.decision`

The decision package is now named `decision`, in code and in the docs. The optional app kit keeps the
name `appkit`.

| Before | After |
|---|---|
| `from laix.core import ...` | `from laix.decision import ...` |
| `from laix.core.contract import ...` | `from laix.decision.contract import ...` |
| `laix/core/` | `laix/decision/` |
| `packages/typescript/laix/src/core/` | `packages/typescript/laix/src/decision/` |
| `docs/02-core/` | `docs/02-decision/` |
| `docs/02-core/03-decision/` | `docs/02-decision/03-decision-shapes/` |
| `examples/python/core/` | `examples/python/decision/` |
| `examples/typescript/core/` | `examples/typescript/decision/` |
| `tests/core/` | `tests/decision/` |

There is no compatibility alias. Update the import path; the record shape, reason codes and public
names are unchanged.

## 0.13.0: planners, policies and app-kit modules are top-level

The decision package no longer nests algorithms under `engines/`, and the app kit no longer has one
`runtime` package.

| Before | After |
|---|---|
| `laix.decision.engines.decision.single.planners` | `laix.decision.planners.single` |
| `laix.decision.engines.decision.single.policies` | `laix.decision.policies` |
| `laix.decision.engines.decision.sequence` | `laix.decision.planners.sequence` |
| `laix.decision.engines.decision.fleet` | `laix.decision.planners.fleet` |
| `laix.decision.engines.decision.history` | `laix.decision.planners.history` |
| `laix.decision.engines.decision.explain` | `laix.decision.planners.explain` |
| `laix.decision.engines.sensing` | `laix.decision.sensing` |
| `laix.decision.engines.learning` | `laix.decision.learning` |
| `laix.decision.engines.evaluation` | `laix.decision.evaluation` |
| `laix.appkit.runtime.decision_runtime` | `laix.appkit.loop.decision_runtime` |
| `laix.appkit.runtime.execution` | `laix.appkit.execution.execution` |
| `laix.appkit.runtime.state` | `laix.appkit.state.state` |

The top-level `from laix import ...` surface is unchanged. Only deep imports move.

## 0.17.3: decision client field parity

`DecisionClient` now keeps the full custom-policy decision: alternatives, attributes, intent, situation
id, event and deadline metadata, revision, status, target and recipients. A host policy no longer loses
those fields on the way out.

The examples and docs were also aligned with the current decision and app-kit surface. No import
changes are required.

## 0.17.2: belief-aware commitments

`CommitmentBeliefPlanner` is additive. It reads completion probabilities from
`attributes["commitment_probabilities"]`, a commitment's `payload["completion_probability"]` or its
`default_probability`, and returns `verify` when the best action is below `verify_below`.

## 0.17.1: sequence trust

`CABBPlanner` and `plan_decisions` / `planDecisions` accept `require_verified` and
`max_verification_age` / `maxVerificationAgeMs`. A scenario can carry commitments owned by another
party; the sequence planner resolves them through `CommitmentGraph` before scoring an option. The
defaults match the single-decision planners.

## 0.17.0: decision extensions

A `verified` commitment without a valid `verified_at` is now untrusted. Set the timestamp when the
host marks a promise verified; a missing or invalid value can no longer satisfy a verified
dependency.

`CommitmentPlanner` alternatives add `rejected_reason_code`; keep using `rejected_because` for
display. `CommitmentResolutionPlanner`, `PortfolioPlanner`, `RiskBoundedPlanner`,
`RevalidationPlanner`, `CaseBasedPlanner` and `ConflictResolutionPlanner` are additive. `LiveCompositePlanner`,
`CAVODPlanner` and `PlanningPolicy` accept the same trust and freshness settings as the commitment
planner.

`policy_iteration` supports infinite-horizon discounted MDPs; finite-horizon models keep using
`value_iteration`.

## 0.16.0: freshness and graph tooling

`CommitmentBlocker.reason` can now be `stale` in addition to `missing`, `open` and `unverified`.
Code that branches on the reason should handle it.

The planner accepts `max_verification_age` (Python) or `maxVerificationAgeMs` (TypeScript). The
default is `None`, so existing decisions do not change until the host opts in.

The graph adds `is_fresh`, `stale_refs`, `validate`, `subgraph`, `neighborhood`, `redacted`,
`to_mermaid` and `to_dot`. The app kit adds `AsyncCommitmentResolver` and
`resolve_commitment_graph_async` / `resolveCommitmentGraphAsync`.

## 0.15.0: configurable commitment verification

`CommitmentPlanner` now takes `require_verified` — a Python keyword argument or the third TypeScript
constructor option. The default stays `True`, so existing behavior is unchanged. Set it to `False`
only when the host accepts reported external commitments.

The result attributes add `commitments_blocked_by`, and alternatives add `blocked_by`. Both are
additive and use `{owner, ledger, id, reason}`.

`CommitmentGraph.from_dict` / `fromDict` round-trips the payload from `to_dict()`.

## 0.14.0: commitment graphs

Commitments can now cross owners. The public names are additive: `CommitmentRef`,
`CommitmentGraph`, `CommitmentBlocker`, `COMMITMENT_SOURCES`, plus the new `Commitment` fields
`owner`, `ledger`, `source`, `verified_at` and `external_depends_on`. Existing commitments still
default to `owner="local"` and `source="local"`.

The commitment modules were split while the feature landed:

| Before | After |
|---|---|
| `domain/commitments/commitment_record.py` | `domain/commitments/commitment.py` |
| `domain/commitments/commitment.py` (ledger) | `domain/commitments/ledger.py` |
| `domain/commitments/in_memory_commitment_store.py` | `domain/commitments/in_memory_store.py` |
| `domain/commitments/file_commitment_store.py` | `domain/commitments/file_store.py` |

TypeScript users can keep importing from `commitments.ts`; it now re-exports `commitment.ts`,
`ledger.ts` and `graph.ts`.

`CommitmentLedger.blocked()` cannot resolve another owner, so it now treats every
`external_depends_on` reference as unresolved. Pass a `CommitmentGraph` when external promises
should count.

## 0.13.1: generated TypeScript declarations

The package now ships declarations at `dist/index.d.ts`, generated from the source. The old
hand-maintained `types.d.ts` is removed. Public import names are unchanged; the difference is that
every public name is now visible to TypeScript.

## Vocabulary migration (0.10.0)

0.10.0 renamed the planning and attention vocabulary. There are no compatibility aliases.

| Before | After |
|---|---|
| `DecisionEngine` | `Planner` |
| `DecisionProblem` | `PlannerInput` |
| `Plan` | `PlannerResult` |
| `EnginePolicy` | `PlannerPolicy` |
| `LiveDecisionEngine` | `LiveCompositePlanner` |
| `Policy` | `DecisionPolicy` |
| `PolicyRegistry` | `DecisionPolicyRegistry` |
| `PolicyError` | `DecisionPolicyError` |
| `Layer` | `DecisionClient` |
| `PlannerScore` | `PlannerBenchmarkRow` |
| `ActionPolicyRequest` | `ActionPolicyInput` |
| `decide_attention` | `decide_signal_attention` |
| `from_attention` | `from_signal_attention` |
| `AttentionDecision` | `SignalAttentionDecision` |
| `AttentionOutcome` | `SignalAttentionOutcome` |
| `OutcomeLog` | `SignalAttentionLog` |
| `Context` | `SignalContext` |
| `Feedback` | `SignalFeedback` |
| `AttentionBudget` | `HumanAttentionBudget` |
| `AttentionEffect` | `HumanAttentionEffect` |
| `AttentionScore` | `HumanAttentionScore` |
| `AttentionWeights` | `HumanAttentionWeights` |
| `attention_effect` | `human_attention_effect` |
| `attention_score` | `human_attention_score` |
| `attention_cost` | `human_attention_cost` |
| `attention_weights` | `human_attention_weights` |
| `attention_budget` | `human_attention_budget` |
| `attention_spent` | `human_attention_spent` |
| `attention_remaining` | `human_attention_remaining` |
| `attention_budget_blocked` | `human_attention_budget_blocked` |
| `attention_budget_exhausted` | `human_attention_budget_exhausted` |
| `attention_aware` | `human_attention_aware` |
| `attention.v1` | `human-attention.v1` |
| `attentionBudget` | `humanAttentionBudget` |
| `CompositeScore.attention` | `CompositeScore.human_attention` |

Result artifacts under `results/` preserve the names from the run that produced them; they are evidence, not the current API.

Paths changed with the names:

| Before | After |
|---|---|
| `core/engines/contract/decision_engine.py` | `decision/contract/planner.py` |
| `core/engines/contract/decision_problem.py` | `decision/contract/planner_input.py` |
| `core/engines/contract/plan.py` | `decision/contract/planner_result.py` |
| `core/engines/contract/engine.py` | `decision/contract/planner_policy.py` |
| `core/engines/live/live_engine.py` | `decision/planners/single/composite/live_composite_planner.py` |
| `core/engines/policies/policy.py` | `decision/policies/decision_policy.py` |
| `core/engines/policies/registry.py` | `decision/policies/decision_policy_registry.py` |
| `appkit/layer.py` | `appkit/decision_client.py` |
| `core/engines/planners/attention/` | `decision/planners/single/human_attention/` |
| `core/engines/signals/input/context.py` | `decision/sensing/signals/input/signal_context.py` |
| `core/engines/signals/input/feedback.py` | `decision/sensing/signals/input/signal_feedback.py` |
| `core/engines/signals/output/decision.py` | `decision/sensing/signals/output/signal_attention_decision.py` |
| `core/outcome_learning/attention/` | `decision/domain/outcomes/signal_attention/` |
| `core/evaluation/attention.py` | `decision/evaluation/cases/signal_attention.py` |
| `core/engines/simulation/planner_score.py` | `decision/evaluation/simulation/planner_benchmark_row.py` |
| `core/engines/signals/attention.v1.json` | `decision/sensing/signals/signal-attention.v1.json` |
| `packages/contracts/attention.v1.json` | `packages/contracts/signal-attention.v1.json` |
| `packages/contracts/attention-bench.v1.json` | `packages/contracts/signal-attention-bench.v1.json` |
| `core/contract/engine.ts` | `decision/contract/planner.ts` |
| `core/live/live-engine.ts` | `decision/planners/single/composite/live-composite-planner.ts` |
| `core/planners/attention/` | `decision/planners/single/human-attention/` |
| `core/policies/registry.ts` | `decision/policies/decision-policy-registry.ts` |
| `appkit/layer.ts` | `appkit/decision-client.ts` |
| `core/signals/attention.ts` | `decision/sensing/signals/signal-attention.ts` |

## Upgrading from a pre-0.10.0 release

0.10.0 separated four layers:

- **Planner** - a strategy;
- **Engine** (now **CompositePlanner**) - a composition;
- **DecisionPolicy** - an integration;
- **Learner** - learning.

| Before | After |
|---|---|
| `UtilityEngine` | `UtilityPlanner` |
| `CommitmentAwareEngine` | `CommitmentPlanner` |
| `ExecutionAwareEngine` | `ExecutionRiskPlanner` |
| `AttentionAwareEngine` | `HumanAttentionPlanner` |
| `MDPEngine` | `MDPPlanner` |
| `POMDPEngine` | `POMDPPlanner` |
| `LiveScore` | `CompositeScore` |
| `compare_engines` / `compareEngines` | `compare_planners` / `comparePlanners` |
| `EngineScore` | `PlannerBenchmarkRow` |
| `FixedActionEngine` | `FixedActionPlanner` |
| `FirstOptionEngine` | `FirstOptionPlanner` |
| `HighestBenefitEngine` | `HighestBenefitPlanner` |
| `run_engine_bench` / `runEngineBench` | `run_planner_bench` / `runPlannerBench` |

Unchanged:

| Surface | Why |
|---|---|
| `LiveCompositePlanner` | it is the composite planner |
| `PlannerPolicy` | it is the policy adapter |
| `UCBBandit` | it is a learner |
| `Planner` | it is the protocol |
| `live_decision` | stable reason code |
| `live`, `glue`, `commitment`, `execution`, `attention`, `utility`, `first`, `benefit` | stable JSON and bench keys |
| `LiveCase`, `LiveBench`, `live_bench` | benchmark terms |
| `benchmarks/live`, `results/live-decision-benchmark` | benchmark names |

Paths also changed:

| Before | After |
|---|---|
| `core/engines/planners/live/` | `decision/planners/single/composite/` |
| `utility/utility.py` | `utility/utility_planner.py` |
| `mdp/mdp.py` | `mdp/mdp_planner.py` |
| `pomdp/pomdp.py` | `pomdp/pomdp_planner.py` |
| `engine_score.py` | `planner_benchmark_row.py` |

No compatibility aliases are provided. The rename is deliberate: two names for one role cause
confusion. Update the import instead of keeping both names.

JSON keys and reason codes are data identifiers; class names are code identifiers. They do not
have to match. For example, the `live` benchmark key maps to `LiveCompositePlanner`, while
`commitment` maps to `CommitmentPlanner`.

## Compatibility rules

- Public entry points, record fields and the decision shape are the compatibility surface.
- Additive fields are preferred.
- Removing or renaming a record field is a schema change and needs a new schema version.
- A change to a reason code is a behaviour change; call it out in the changelog.
- Python and TypeScript move together for a release. A parity difference is a regression.

## Deprecation policy

1. Mark the old surface in the docs and changelog.
2. Keep it working for at least one minor release when practical.
3. Add the replacement and a migration example.
4. Remove it only with a schema or major-version change.

## Data migration

Decision records, checkpoints, commitment ledgers, experience state and outcome stores are
owned by the host. When their shape changes:

- back up the store before migrating;
- write a one-way migration script with a dry run;
- keep the old records readable during the transition;
- verify a migrated record with `verify_record` if it carries a fingerprint;
- record the migration in the changelog and the data-access note.

## Rollback

- Keep the previous package version pinned.
- Keep the previous policy version available.
- Keep old records until the new version has been stable for the retention window.
- If a rollback changes the record shape, keep both readers during the transition.

## Current status

The current release is `0.17.3`. Add a new entry here when a release requires host changes; keep it
short and concrete.
