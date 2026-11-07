# Migration and deprecation

LAIX is pre-1.0. Treat every minor release as potentially breaking, even when the package
version only moves by a small amount. This page is the upgrade path; the version axes are in
[Versioning](versioning.md).

## Before an upgrade

1. Read the release section in [CHANGELOG.md](../../CHANGELOG.md).
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

## Planner naming migration (0.10.0)

0.10.0 separates four layers:

- **Planner** — a strategy;
- **Engine** — a composition;
- **Policy** — an integration;
- **Learner** — learning.

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
| `EngineScore` | `PlannerScore` |
| `FixedActionEngine` | `FixedActionPlanner` |
| `FirstOptionEngine` | `FirstOptionPlanner` |
| `HighestBenefitEngine` | `HighestBenefitPlanner` |
| `run_engine_bench` / `runEngineBench` | `run_planner_bench` / `runPlannerBench` |

Unchanged:

| Surface | Why |
|---|---|
| `LiveDecisionEngine` | it is the composition engine |
| `EnginePolicy` | it is the policy adapter |
| `UCBBandit` | it is a learner |
| `DecisionEngine` | it is the protocol |
| `live_decision` | stable reason code |
| `live`, `glue`, `commitment`, `execution`, `attention`, `utility`, `first`, `benefit` | stable JSON and bench keys |
| `LiveCase`, `LiveBench`, `live_bench` | benchmark terms |
| `benchmarks/live`, `results/live-decision-benchmark` | benchmark names |

Paths also changed:

| Before | After |
|---|---|
| `core/engines/planners/live/` | `core/engines/live/` |
| `utility/utility.py` | `utility/utility_planner.py` |
| `mdp/mdp.py` | `mdp/mdp_planner.py` |
| `pomdp/pomdp.py` | `pomdp/pomdp_planner.py` |
| `engine_score.py` | `planner_score.py` |

No compatibility aliases are provided. The rename is deliberate: two names for one role cause
confusion. Update the import instead of keeping both names.

JSON keys and reason codes are data identifiers; class names are code identifiers. They do not
have to match. For example, the `live` benchmark key maps to `LiveDecisionEngine`, while
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

The current release is `0.10.0`. The planner/engine/policy/learner naming change is the first
migration entry that requires host changes. Add a new entry here when a release requires host
changes; keep it short and concrete.
