# Evaluation

LAIX has three kinds of checks.

| Check | Location |
|---|---|
| Attention behaviour | `packages/contracts/attention.v1.json` |
| Attention outcomes | `packages/contracts/attention-bench.v1.json` |
| Every decision class | `python -m laix.appkit.bench`, `npm run bench` |
| Training-free live decisions | `python -m laix.appkit.bench --live` |

The JSON schemas in `packages/contracts/` describe the record shapes.

## Run

```powershell
# Python
cd packages/python/laix
py -m pytest -q
py -m laix.appkit.bench

# TypeScript
cd packages/typescript/laix
npm.cmd test
npm.cmd run bench
npm.cmd run conformance
```

Conformance compares the attention decisions with the shared vector file.

## Next evaluation work

- A held-out set.
- Real user outcomes.
- A causal study.
- Live sensing and sub-second cases.

These checks show whether a change altered behaviour. User studies show how the layer performs in
the real world.
