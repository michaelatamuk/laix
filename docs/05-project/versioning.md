# Versioning

Several things move independently.

| Thing | Version | Source |
|---|---|---|
| Python package | `0.9.0` | `packages/python/laix/pyproject.toml` |
| TypeScript package | `0.9.0` | `packages/typescript/laix/package.json` |
| Record schema | `0.8.0` | `core/support/version.py`, `contracts.ts` |
| Rule sets | `0.8.0` | policy versions and vectors |
| Attention vectors | `0.8.0` | `attention.v1.json` and conformance fixtures |

## When to bump

- **Package** — any user-visible change, feature or fix. Both packages move together for a release.
- **Record schema** — a record shape changes. Regenerate `laix-v1.schema.json` and update the
  contract page.
- **Rule sets or attention vectors** — a rule, threshold or labelled vector changes behaviour.

A code change that leaves a record shape unchanged leaves the schema unchanged.

## Releases

1. Update both package versions and `CHANGELOG.md`.
2. Run the full test, bench, conformance and example checks.
3. Commit the release.
4. Tag `vX.Y.Z` and push the tag. The release workflow builds Python and TypeScript packages.
5. Pin the new tag in the [quickstart](../01-start/quickstart.md) install command and the release
   notes.

## Changelog

`CHANGELOG.md` has one section per released version. Unreleased work stays under `Unreleased`
until the version and tag are cut.

## Compatibility

The public entry points, record fields and decision shape are the compatibility surface. Internal
modules can move. Additive fields are preferred; removing or renaming a record field is a schema
change.
