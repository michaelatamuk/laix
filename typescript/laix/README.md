# laix (TypeScript)

One package for the LAIX decision layer: the attention policy and the decision record, behind one
entry point. The package uses language features only and takes generic inputs.

```ts
import { Layer } from "laix";

const layer = new Layer();
const decisions = layer.decide({
  subject: "one signal",
  at: "2026-11-01T10:00:00Z",
  signals: [{ id: "s-1", kind: "k", severity: "high", confidence: 0.9 }],
  context: { now: "2026-11-01T10:00:00Z", quietHours: null },
});
```

`Layer.decide` accepts either `signals` + `context` or `situation` + `options`, and returns the same
`LayerDecision` shape for both.

The package also exports:

- `decide(context, signals)` — the attention policy;
- `isQuietHours`, `score`, `costOfWaiting`, `OutcomeLog`;
- `createDecisionRecord`, `approveRecord`, `rejectRecord`, `markExecuted`, `undoRecord`,
  `verifyRecord`, `fingerprint`.

The attention policy passes the same 23 cases as the Python policy. The decision record lifecycle
is:

```
draft -> approved -> executed -> undone
  |
  +-> rejected
```

## Test

```powershell
npm.cmd test
npm.cmd run conformance
```

`npm.cmd run conformance` compares every attention decision against
`contracts/attention.v1.json` and exits non-zero on a mismatch.
