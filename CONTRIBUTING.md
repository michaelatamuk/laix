# Contributing to LAIX

Thanks for helping. LAIX is a small, opinionated codebase: the decision contract, the
planner surface and the Python/TypeScript parity are the product. Changes that keep those
three coherent are welcome.

## Before you start

- Read the [documentation index](docs/README.md) and the
  [repository structure](docs/05-project/01-repository/01-repository-structure.md).
- Open an issue before a large change, a new public class or a new dependency.
- Report security issues through [SECURITY.md](SECURITY.md), not a public issue.
- By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Python 3.11 or newer and Node 22 or newer are required.

```powershell
git clone https://github.com/michaelatamuk/laix.git
cd laix

python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pytest ruff jsonschema
python -m pip install -e packages/python/laix

cd packages/typescript/laix
npm ci
```

The Python package uses the standard library. The TypeScript package has no runtime
dependencies.

## Repository layout

| Folder | Contents |
|---|---|
| `packages/python/laix/` | Python package and tests |
| `packages/typescript/laix/` | TypeScript package and tests |
| `packages/contracts/` | shared schemas and conformance vectors |
| `docs/` | numbered guides and reference pages |
| `examples/` | runnable Python and TypeScript examples |
| `benchmarks/` | versioned corpus and external comparison harness |
| `data/` | optional external validation material |
| `results/` | generated benchmark evidence |
| `scripts/` | CI, benchmark, validation and asset tooling |

## Design rules

- **One class per file.** Functions may share a small module with their owner.
- **Group by role**, not by feature accident: `contract/`, `planners/`, `live/`, `simulation/`,
  `learning/`, `bench/`, `commitments/`, `perception/`, `policies/`, `signals/`.
- **Use one name per role.** `Planner` is the strategy and the protocol, `CompositePlanner` is a
  composition, `DecisionPolicy` is an integration, and `Learner` is learning. Do not call a
  composite planner an engine.
- **Keep the public API in `__init__.py` and `index.ts`.**
- **Mirror the Python surface in TypeScript.** Parity is tested, not assumed.
- **Use generic vocabulary.** No app, domain or vendor names in the decision layer.
- **Training-free by default.** A planner may use a model the host supplies; the contract
  does not change.
- **Keep the host in control of execution, storage, delivery and data.**

## Checks

Run the checks that cover your change. Before a pull request, run the full set.

Python:

```powershell
cd packages/python/laix
python -m pytest -q
python -m ruff check .
python -m laix.appkit.bench
```

TypeScript:

```powershell
cd packages/typescript/laix
npm run typecheck
npm run typecheck:declarations
npm test
npm run check:consumer
npm run bench
npm run conformance
npm run live-bench
```

Repository checks, from the root:

```powershell
python scripts/ci/check_docs_links.py
bash scripts/novelty/reproduce.sh
```

The live benchmark, analysis and ablations are also documented in
[Testing](docs/05-project/02-quality/01-testing.md).

## Change workflow

1. Create a branch from `main`.
2. Make the smallest coherent change.
3. Add or update tests.
4. Update the docs when behaviour, names or paths change.
5. Add a `CHANGELOG.md` entry under `Unreleased`.
6. Run the checks above.
7. Open a pull request with the problem, the change and the evidence.

## Pull request checklist

- [ ] Tests cover the change.
- [ ] Python and TypeScript still agree, or the difference is documented.
- [ ] Public imports still work.
- [ ] Docs and relative links are updated.
- [ ] `CHANGELOG.md` is updated.
- [ ] No secrets, personal data or generated participant data are committed.

## Commit messages

Use the imperative mood and a short prefix:

```text
feat: add a commitment-aware planner
fix: keep the attention budget after a revision
refactor: group the novelty scripts by method
docs: explain the decision runtime
test: cover the unknown receipt path
chore: update the CI matrix
```

The body should say why the change exists, not repeat the diff.

## Documentation

- Numbered sections are read in order; reference sections stay unnumbered.
- Use full class names in prose and tables (`LiveCompositePlanner`, `UtilityPlanner`); reserve short
  keys such as `live` for stable JSON and CLI identifiers.
- Keep one H1 per page.
- Use relative links and run `python scripts/ci/check_docs_links.py`.
- Put new pages in the right section and add them to [docs/README.md](docs/README.md).

## Release

The release process, compatibility rules and schema versions are in
[Versioning](docs/05-project/03-release/01-versioning.md). Tag releases from `main`.

## Security

Read [SECURITY.md](SECURITY.md) before reporting a vulnerability. Keep exploit details out of
public issues.
