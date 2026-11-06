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
- Do not delete old records until the new version has been stable for the retention window.
- If a rollback changes the record shape, keep both readers during the transition.

## Current status

The current release is `0.9.0`. There are no historical migration entries yet. Add one here
when a release requires host changes; keep it short and concrete.
