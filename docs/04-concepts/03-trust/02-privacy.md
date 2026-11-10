# Privacy and trust

LAIX is the live decision layer for AI agents that act in the real world. The host
owns the data, the transport and the storage.

## What the decision layer needs

- generic subjects, verbs and reasons;
- comparable numbers for benefit, cost, risk and urgency;
- references to evidence;
- limits the app is willing to accept.

Keep secrets, credentials and raw customer data in the host. Pass references in `attributes`,
`evidence`, `intent.args` or `rationale`.

## What crosses the boundary

| Data | What LAIX needs | What the host keeps |
|---|---|---|
| Subject | A generic label or id. | The customer, account, case or asset behind it. |
| Situation | Beliefs, goals and constraints as values. | Raw text, documents, images and transcripts. |
| Options | Ids, benefit, cost, risk and reversibility. | The domain meaning and the execution handler. |
| Evidence | `EvidenceRef` ids, quotes and sources. | The source system and access control. |
| Decision | Verb, reason, score, confidence and action id. | The UI, the message and the channel. |
| Receipt | Status, actor and detail. | Credentials, provider payloads and retries. |
| Outcome | Metric, before/after and label. | The measurement pipeline and raw data. |

## Sharing a decision

`GroupPolicy` is the boundary for sharing. It can:

- set `target` and `recipients`;
- remove private keys from `attributes`, recursively;
- remove private keys from `intent.args` and alternative payloads;
- drop evidence by id, kind or source;
- replace `rationale` and `undo_hint`.

Apply `GroupPolicy` outermost when its target and recipients must win. Masking applies in either
order. The policy contract is in [Policies](../../02-decision/03-decision-shapes/06-policies/README.md).

## Stored data

Decision records, checkpoints, commitment ledgers, experience state and outcomes can contain
sensitive fields. The host secures them. LAIX defines the shapes and the save/load contracts; the host
owns the database.

| Store | What it may contain | Owner |
|---|---|---|
| `StateStore` | Goals, beliefs, observations and history. | Host. |
| `StreamCheckpointStore` | Watermark, counters, buffered decisions and traces. | Host. |
| `CommitmentStore` | Promises, due times, dependencies and payload. | Host. |
| `OutcomeStore` | Metrics, labels, attribution and evidence refs. | Host. |
| Decision records | Evidence, approval, audit events and undo state. | Host. |

The store contracts are in [Stores](../../03-appkit/04-connect/01-stores.md).

## Telemetry

`prometheus(stats)` exports counters such as decided, dropped, suppressed, duplicates, shed and
latency percentiles. It exports counters, not payloads. Traces can contain ids and reasons; treat them
as metadata with the same care as records.

- Do not put customer text, secrets or raw prompts in metric names or labels.
- Keep trace ids and decision ids; drop payloads unless the host needs them.
- Apply the same retention rule to traces, metrics and records.
- Alert on rates, not on payload content.

See [Metrics](../../03-appkit/05-operate/02-metrics.md).

## Trust boundary

The decision layer runs on standard-library data and an injected clock. The optional app kit adds execution,
streaming, stores, delivery and platform ports. Every external effect stays in host code.

LAIX does not authenticate the caller, authorize an action, encrypt a store or filter a prompt. Those
are host responsibilities; see [Security](01-security.md).

## Host checklist

- [ ] Keep secrets and raw customer data out of requests, decisions and logs.
- [ ] Pass references, not payloads, where possible.
- [ ] Apply `GroupPolicy` before sharing a decision outside its target.
- [ ] Encrypt stores and restrict access.
- [ ] Define retention and deletion for records, traces, metrics and outcomes.
- [ ] Keep telemetry to ids, reasons and counters.
- [ ] Re-check authorization in the execution adapter.

## Related

- [Security](01-security.md) - threat model and controls.
- [Stores](../../03-appkit/04-connect/01-stores.md) - persistence contracts.
- [Execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md) - the write boundary.
- [Metrics](../../03-appkit/05-operate/02-metrics.md) - counters and alerts.
- [Glossary](../../05-reference/01-glossary.md) - the vocabulary.
