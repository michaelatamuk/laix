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

## Vocabulary migration (next release)

The next release renames the planning and attention vocabulary. There are no compatibility aliases.

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
| `core/engines/contract/decision_engine.py` | `core/engines/contract/planner.py` |
| `core/engines/contract/decision_problem.py` | `core/engines/contract/planner_input.py` |
| `core/engines/contract/plan.py` | `core/engines/contract/planner_result.py` |
| `core/engines/contract/engine.py` | `core/engines/contract/planner_policy.py` |
| `core/engines/live/live_engine.py` | `core/engines/planners/composite/live_composite_planner.py` |
| `core/engines/policies/policy.py` | `core/engines/policies/decision_policy.py` |
| `core/engines/policies/registry.py` | `core/engines/policies/decision_policy_registry.py` |
| `appkit/layer.py` | `appkit/decision_client.py` |
| `core/engines/planners/attention/` | `core/engines/planners/human_attention/` |
| `core/engines/signals/input/context.py` | `core/engines/signals/input/signal_context.py` |
| `core/engines/signals/input/feedback.py` | `core/engines/signals/input/signal_feedback.py` |
| `core/engines/signals/output/decision.py` | `core/engines/signals/output/signal_attention_decision.py` |
| `core/outcome_learning/attention/` | `core/outcome_learning/signal_attention/` |
| `core/evaluation/attention.py` | `core/evaluation/signal_attention.py` |
| `core/engines/simulation/planner_score.py` | `core/engines/simulation/planner_benchmark_row.py` |
| `core/engines/signals/attention.v1.json` | `core/engines/signals/signal-attention.v1.json` |
| `packages/contracts/attention.v1.json` | `packages/contracts/signal-attention.v1.json` |
| `packages/contracts/attention-bench.v1.json` | `packages/contracts/signal-attention-bench.v1.json` |
| `core/contract/engine.ts` | `core/contract/planner.ts` |
| `core/live/live-engine.ts` | `core/planners/composite/live-composite-planner.ts` |
| `core/planners/attention/` | `core/planners/human-attention/` |
| `core/policies/registry.ts` | `core/policies/decision-policy-registry.ts` |
| `appkit/layer.ts` | `appkit/decision-client.ts` |
| `core/signals/attention.ts` | `core/signals/signal-attention.ts` |

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
| `core/engines/planners/live/` | `core/engines/planners/composite/` |
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

The current release is `0.10.0`. The next release includes the vocabulary migration above. The 0.10.0
planner naming change was the first migration entry that required host changes. Add a new entry here
when a release requires host changes; keep it short and concrete.
