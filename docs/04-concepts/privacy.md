# Privacy and trust

LAIX is a decision layer. The host owns the data, the transport and the storage.

## What the layer needs

- generic subjects, verbs and reasons;
- comparable numbers for benefit, cost, risk and urgency;
- references to evidence, not the raw evidence itself when possible;
- limits the app is willing to accept.

Do not put secrets, credentials or raw customer data in `attributes`, `evidence`, `intent.args` or
`rationale` unless the decision is allowed to carry them.

## Sharing a decision

`GroupPolicy` is the boundary for sharing. It can:

- set `target` and `recipients`;
- remove private keys from `attributes`, recursively;
- remove private keys from `intent.args` and alternative payloads;
- drop evidence by id, kind or source;
- replace `rationale` and `undo_hint`.

Apply `GroupPolicy` outermost when its target and recipients must win. Masking applies in either
order.

## Stored data

Decision records, checkpoints, commitment ledgers, experience state and outcomes can contain
sensitive fields. The host secures them. LAIX defines the shapes and the save/load contracts; it does
not own a database.

## Telemetry

`prometheus(stats)` exports counters such as decided, dropped, suppressed, duplicates, shed and
latency percentiles. It does not include request payloads. Traces can contain ids and reasons; treat
them as metadata with the same care as records.

## Trust boundary

The core has no network, database or clock of its own. The optional app kit adds execution,
streaming, stores, delivery and platform ports. Every external effect stays in host code.
