# Versioning

Several things move independently. A package release does not always change the record schema, and a
rule change does not always change the package version.

| Thing | Current | Source |
|---|---|---|
| Python package | `0.17.1` | `packages/python/laix/pyproject.toml` |
| TypeScript package | `0.17.1` | `packages/typescript/laix/package.json` |
| Record schema | `0.8.0` | `decision/support/version.py`, `contracts.ts` |
| Rule sets | `0.8.0` | policy versions and vectors |
| Signal-attention vectors | `0.8.0` | `signal-attention.v1.json` and conformance fixtures |
| Reason-code registry | `1.1.0` | `packages/contracts/reason-codes.v1.json` |

## The axes

| Axis | What it covers | When it changes |
|---|---|---|
| Package version | The Python and TypeScript packages. | Any user-visible feature, fix or behaviour change. |
| Record schema | Field names, JSON keys, types and allowed values. | A record shape changes. |
| Rule set | DecisionPolicy names, thresholds and reason codes. | A rule changes behaviour. |
| Signal-attention vectors | The shared attention conformance cases. | A labelled vector or expected decision changes. |
| Reason-code registry | The stable reason codes an app branches on. | A code is added, removed or renamed. |

A code change that leaves a record shape unchanged leaves the schema unchanged. A new optional field
is additive; a removed or renamed field is a schema change.

## Before 1.0

LAIX is pre-1.0. Treat every minor release as potentially breaking, even when the package version only
moves by a small amount. Read [Migration](02-migration.md) before an upgrade, and keep the previous
package and policy versions available for rollback.

## When to bump

- **Package** - any user-visible change, feature or fix. Both packages move together for a release.
- **Record schema** - a record shape changes. Regenerate `laix-v1.schema.json` and update
  [Records and schema](../../02-decision/01-contract/03-records.md).
- **Rule sets or signal-attention vectors** - a rule, threshold or labelled vector changes behaviour.
- **Reason code** - treat it as a behaviour change, update
  [`reason-codes.v1.json`](../../../packages/contracts/reason-codes.v1.json) and call it out in the
  changelog.

## Releases

1. Update both package versions, `CITATION.cff`, `SECURITY.md` and `CHANGELOG.md`.
2. Run the full test, bench, conformance and example checks. See [Testing](../02-quality/01-testing.md).
3. Commit the release.
4. Tag `vX.Y.Z` and push the tag. The release workflow builds Python and TypeScript packages.
5. Optionally publish the packages to PyPI and npm with the manual [Publishing](03-publishing.md) workflow.
6. Pin the new tag in the [quickstart](../../01-start/02-first-steps/01-quickstart.md) install command and the release
   notes.

## Changelog

[`CHANGELOG.md`](../../../CHANGELOG.md) has one section per released version. Unreleased work stays
under `Unreleased` until the version and tag are cut.

A changelog entry states:

- what changed;
- whether the package, schema, rule set or vectors moved;
- what the host must do;
- whether the change is breaking.

## Compatibility

The public entry points, record fields and decision shape are the compatibility surface. Internal
modules can move. Additive fields are preferred; removing or renaming a record field is a schema
change.

Python and TypeScript move together for a release. A parity difference is a regression. The shared
vectors in `packages/contracts/` are the reference for both packages.

## Related

- [Migration](02-migration.md) - the upgrade path and data migration.
- [Testing](../02-quality/01-testing.md) - the checks before a release.
- [Records and schema](../../02-decision/01-contract/03-records.md) - the schema workflow.
- [Changelog](../../../CHANGELOG.md) - the release history.
