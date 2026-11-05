# Testing

CI runs the same checks locally.

## Python

```powershell
cd packages/python/laix
python -m pytest -q
ruff check .
python -m laix.appkit.bench
```

With `uv` from the repository root:

```powershell
uv run --directory packages/python/laix --with pytest python -m pytest -q
uvx ruff check packages/python/laix
```

Python examples:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
Get-ChildItem examples/python -Recurse -Filter *.py | ForEach-Object { py $_.FullName }
```

`tests/test_examples.py` also runs every Python example.

## TypeScript

```powershell
cd packages/typescript/laix
npm ci
npm run typecheck
npm run typecheck:declarations
npm test
npm run bench
npm run conformance
```

TypeScript examples:

```powershell
Get-ChildItem examples/typescript -Recurse -Filter *.mts | ForEach-Object {
    node --experimental-strip-types $_.FullName
}
```

## Docs

```powershell
python scripts/check_docs_links.py
```

The check resolves relative links across `docs/`, `examples/` and every README.

## What covers what

| Check | Covers |
|---|---|
| `pytest` | contracts, policies, planners, app kit, schema, examples |
| `ruff check` | Python syntax, undefined names and unused imports |
| `tsc` | TypeScript source and public declaration syntax/types |
| `npm test` | TS contracts, conformance, parity, streaming, execution, planners |
| `npm run bench` | 10 suites and 25 deterministic cases |
| `npm run conformance` | 24 shared attention decisions |
| examples | every runnable Python and TypeScript example |
| docs links | relative links in docs, examples and README files |

## CI

`.github/workflows/ci.yml` runs Python on 3.11 and 3.13, TypeScript on Node 22 and 24, and the docs
link check. `.github/workflows/release.yml` runs the same checks before building a tagged release.
