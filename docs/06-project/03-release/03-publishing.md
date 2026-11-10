# Publishing

GitHub releases are created by the tag workflow. Registry publishing is a separate, manual
workflow. A release can be complete on GitHub before it is available on PyPI or npm.

## Before publishing

1. Both package versions and `CHANGELOG.md` are current.
2. `vX.Y.Z` is tagged and the GitHub release exists.
3. The registry prerequisites below are configured once.

## PyPI

The Python package name is `laix`. Use PyPI trusted publishing:

- owner: `michaelatamuk`
- repository: `laix`
- workflow: `publish.yml`
- environment: `pypi`

The workflow builds the wheel and source distribution, then publishes with
`pypa/gh-action-pypi-publish`. No API token is stored in the repository.

## npm

The TypeScript package name is `laix`. Confirm the name is available, or scope it before the first
publish. The package builds ESM output and declarations to `dist/` and points its types at
`dist/index.d.ts`.

Use one of these:

- add an `NPM_TOKEN` repository secret with publish access;
- configure npm trusted publishing for this repository and remove the `NODE_AUTH_TOKEN` environment
  variable from `publish.yml`.

The workflow runs the build, tests and conformance suite before `npm publish --provenance`.

## Publish

Run the workflow manually:

```powershell
gh workflow run publish.yml -f target=both
gh run watch
```

Use `target=python` or `target=npm` to publish only one package.

## Verify

```powershell
python -m pip install "laix==0.17.0"
npm view laix version
npm install laix@0.17.0
```

Then run one of the examples against the installed package, not the source tree.

## Rollback

A published version cannot be reused, even after it is removed. If a release is wrong:

1. yank the PyPI release or deprecate the npm version;
2. publish a patch version with the fix;
3. keep the previous tag and package available for rollback.

Do not delete and re-tag a published version.

## Related

- [Versioning](01-versioning.md) - the version axes and release steps.
- [Migration](02-migration.md) - upgrade and rollback guidance.
- [Testing](../02-quality/01-testing.md) - the checks before a release.
