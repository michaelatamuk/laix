# Privacy and trust

LAIX is the decision runtime for AI agents and automations that act in the real world. The host owns the data, the transport and the
storage.

## What the runtime needs

- generic subjects, verbs and reasons;
- comparable numbers for benefit, cost, risk and urgency;
- references to evidence;
- limits the app is willing to accept.

Keep secrets, credentials and raw customer data in the host. Pass references in `attributes`,
`evidence`, `intent.args` or `rationale`.

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
sensitive fields. The host secures them. LAIX defines the shapes and the save/load contracts; the
host owns the database.

## Telemetry

`prometheus(stats)` exports counters such as decided, dropped, suppressed, duplicates, shed and
latency percentiles. It exports counters. Traces can contain ids and reasons; treat them as
metadata with the same care as records.

## Trust boundary

The core runs on standard-library data and an injected clock. The optional app kit adds execution,
streaming, stores, delivery and platform ports. Every external effect stays in host code.
